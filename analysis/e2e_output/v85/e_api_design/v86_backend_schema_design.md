# V86 后端存储结构设计方案

> 任务：`E_V85_READONLY_API_AND_V86_BACKEND_DESIGN` · T2.2
> 分支：`feature/v85-chart-template`
> 输入参考：`v86_alias_engine_full_design.md`（DSHE 产物，未修改）、`v86_gate_fusion_framework.md`
> 未就绪依赖：`v86_init_backlog_total.md`（HERMES 产物，T1 依赖，未就绪时以本设计中的占位约定推进；标记 `DEPENDENCY_NOT_READY=TRUE`）
> 约束：本设计**仅定义 V86 存储结构**，不落地任何业务结果；V85 数据保持只读。

---

## 1. 设计目标与非目标

### 1.1 目标
1. **新别名引擎存储**：把 V85 的 CSV 别名库演进为可版本化、可回滚的规范别名映射表
2. **规则版本管理**：黑名单规则、模糊匹配规则、Gate 配置全链路可追溯
3. **Gate 结果存储**：每次 Gate 运行产生不可变记录，支持对比与回滚判定
4. **审计与幂等**：所有写入有 origin/version/payload 三元组，重放安全

### 1.2 非目标
- ❌ 不替换现有 `indicators_v1.json`（V86 沿用）
- ❌ 不重写黑名单为数据库表（黑名单保持 JSON 冻结文件，DB 只存"运行时命中"）
- ❌ 不引入时序数据入库（保持 zhiji API 独立通道）
- ❌ 不支持跨租户（V86 面向内部评审，单租户）

---

## 2. 数据分域

| 域 | 内容 | 生命周期 | 存储介质 |
|---|---|---|---|
| **别名域** | alias_mapping / alias_variant / alias_source | 版本化演进 | 关系型（PostgreSQL） |
| **规则域** | rule_registry / rule_version | 版本化演进 | 关系型 |
| **运行域** | gate_run / gate_result / task_run | 不可变追加 | 关系型 + 冷备 Parquet |
| **审计域** | audit_log | 不可变追加 | 关系型 |
| **配置域** | config_snapshot | 版本化 | 关系型 |

---

## 3. 表结构（DDL）

### 3.1 别名域

#### `alias_mapping`（规范别名映射，唯一真源）
```sql
CREATE TABLE alias_mapping (
    id                    BIGSERIAL PRIMARY KEY,
    alias_norm            TEXT NOT NULL,          -- 归一化后的原始串（NFKC + 全角转半角 + 去空白）
    canonical_key         TEXT NOT NULL,          -- 规范键（如 cu_23_comex_close）
    canonical_name        TEXT NOT NULL,          -- 规范中文名
    variety_family        TEXT,                    -- 品种族（CU/AL/NI/SI/SN/LC/AO/PB/ZN）
    metric_noun           TEXT,                    -- 度量名词（价格/库存/产量/...）
    variety_token         TEXT,                    -- 品种 token
    alias_type            TEXT NOT NULL,           -- exact / cross_report_synonym / mixed_script / numeric_suffix / cross_variety
    relation              TEXT NOT NULL,           -- canonical_conflict / self_pair / cross_pair
    confidence            NUMERIC(5,4) NOT NULL DEFAULT 0.5500,
    status                TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / rejected / deprecated
    status_reason         TEXT,
    approved_by           TEXT,
    approved_at           TIMESTAMPTZ,
    alias_source          TEXT,                    -- INDICATORS_V1_NAME / THS_MATCHED / HUMAN_REVIEW / CROSS_REPORT
    alias_id              TEXT NOT NULL UNIQUE,    -- A-00001 格式
    version               INT NOT NULL DEFAULT 1,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- V85 → V86 迁移字段
    v85_alias_id          TEXT,                    -- V85 ALIAS-0001 格式
    v85_confidence        NUMERIC(5,4),

    CONSTRAINT chk_confidence_range CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT chk_status CHECK (status IN ('pending','approved','rejected','deprecated'))
);
CREATE INDEX idx_alias_norm ON alias_mapping(alias_norm);
CREATE INDEX idx_canonical ON alias_mapping(canonical_key, canonical_name);
CREATE INDEX idx_status ON alias_mapping(status, variety_family);
```

**设计要点**：
- `alias_norm` 归一化后作为查询键；`canonical_key` 用 `indicators_v1.json` 的短名（`cu_23_comex_close`），便于和指标库对齐
- `status` 四态：`pending`（待审）→ `approved`/`rejected`；再演进 `deprecated`。V86 引擎只加载 `approved`
- `version` 用于冲突时的版本对齐；重审同一 `alias_norm` 递增 version 而不是覆盖
- `v85_alias_id` / `v85_confidence` 记录迁移来源，用于 V85→V86 对齐校验

#### `alias_variant`（同一 alias_norm 下的多形态）
```sql
CREATE TABLE alias_variant (
    id                    BIGSERIAL PRIMARY KEY,
    alias_id              TEXT NOT NULL REFERENCES alias_mapping(alias_id),
    raw_form              TEXT NOT NULL,          -- 原始形态（如 "COMEX:铜:主力合约:收盘价(日"）
    script_class          TEXT,                   -- zh_CN / en / mixed
    char_count            INT,
    seen_in               TEXT[],                 -- 出现过的场景（THS_TEMPLATE / INDICATORS_V1 / HUMAN_INPUT）
    first_seen_at         TIMESTAMPTZ,
    last_seen_at          TIMESTAMPTZ,
    PRIMARY KEY (id),
    UNIQUE (alias_id, raw_form)
);
CREATE INDEX idx_variant_alias ON alias_variant(alias_id);
```

#### `alias_source`（源引用）
```sql
CREATE TABLE alias_source (
    id                    BIGSERIAL PRIMARY KEY,
    alias_id              TEXT NOT NULL REFERENCES alias_mapping(alias_id),
    source_system         TEXT NOT NULL,          -- indicators_v1 / ths_template / hermes_mapping / human
    source_ref            TEXT NOT NULL,          -- 具体引用（如 "indicators_v1.json#/indicators/cu_23_comex_close"）
    source_version        TEXT,                   -- 源版本号
    snapshot_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_source_alias ON alias_source(alias_id);
```

### 3.2 规则域

#### `rule_registry`（规则注册表：一个 rule_id 一行）
```sql
CREATE TABLE rule_registry (
    rule_id               TEXT PRIMARY KEY,       -- BL-001 / BL-019a / FUZZY-001 / GATE-007
    rule_kind             TEXT NOT NULL,          -- blacklist / fuzzy_match / gate
    name                  TEXT NOT NULL,
    category              TEXT,                   -- 供需口径 / 库存口径 / ...
    severity              TEXT,                   -- P0 / P1 / P2
    description          TEXT,
    status                TEXT NOT NULL DEFAULT 'draft',  -- draft / active / paused / deprecated
    created_by            TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_rule_kind ON rule_registry(rule_kind, status);
```

#### `rule_version`（规则版本快照：不可变）
```sql
CREATE TABLE rule_version (
    id                    BIGSERIAL PRIMARY KEY,
    rule_id               TEXT NOT NULL REFERENCES rule_registry(rule_id),
    version               INT NOT NULL,           -- 递增
    payload               JSONB NOT NULL,         -- 规则完整定义（patterns、threshold、severity 等）
    diff_from_prev        TEXT,                   -- 自然语言摘要
    change_type           TEXT NOT NULL,          -- initial / minor / major / hotfix / deprecate
    author                TEXT,
    approved_by           TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at          TIMESTAMPTZ,            -- 生效时间（可能晚于创建）
    deactivated_at        TIMESTAMPTZ,
    CONSTRAINT uq_rule_version UNIQUE (rule_id, version),
    CONSTRAINT chk_change_type CHECK (change_type IN ('initial','minor','major','hotfix','deprecate'))
);
CREATE INDEX idx_rule_version_rule ON rule_version(rule_id, activated_at DESC);
```

**版本策略**：
- 每次规则修改都生成新 `version`，历史版本永不删除
- `activated_at` 与 `deactivated_at` 之间的时段视为规则生效期
- Gate 与回放运行必须记录当时生效的 `rule_version`（见 §3.3）

### 3.3 运行域

#### `gate_run`（一次 Gate 运行的元数据）
```sql
CREATE TABLE gate_run (
    run_id                TEXT PRIMARY KEY,       -- GATE-2026-10-01T162000-XXXX
    version_tag           TEXT NOT NULL,          -- v85.0 / v86.0-alpha
    commit_sha            TEXT NOT NULL,
    branch                TEXT,
    gate_config_version   INT NOT NULL,           -- 引用的 regression_gate_config.json 版本
    engine_variant        TEXT,                   -- base / f1 / f3 / f3+f4（V86 引擎变体）
    triggered_by          TEXT,
    started_at            TIMESTAMPTZ NOT NULL,
    finished_at           TIMESTAMPTZ,
    status                TEXT NOT NULL DEFAULT 'running',  -- running / passed / failed / aborted
    total_cases           INT,
    passed_cases          INT,
    failed_cases          INT,
    p0_interception_rate  NUMERIC(5,4),           -- P0 拦截率
    boundary_fp_count     INT,
    notes                 TEXT
);
CREATE INDEX idx_gate_run_version ON gate_run(version_tag, started_at DESC);
```

#### `gate_result`（Gate 单项结果）
```sql
CREATE TABLE gate_result (
    id                    BIGSERIAL PRIMARY KEY,
    run_id                TEXT NOT NULL REFERENCES gate_run(run_id),
    gate_id               TEXT NOT NULL,          -- G1 / G2 / ... / G14
    gate_name             TEXT,
    expected              JSONB,
    actual                JSONB,
    verdict               TEXT NOT NULL,          -- PASS / FAIL / N/A
    fail_reason           TEXT,
    detail                JSONB,                  -- 详细用例级结果
    evaluated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (run_id, gate_id)
);
CREATE INDEX idx_gate_result_run ON gate_result(run_id);
CREATE INDEX idx_gate_result_gate ON gate_result(gate_id, verdict);
```

#### `task_run`（异步任务运行记录，V86 专用）
```sql
CREATE TABLE task_run (
    task_id               TEXT PRIMARY KEY,       -- TASK-DH-2026-10-01-00001
    task_type             TEXT NOT NULL,          -- dshb_rule_eval / dshe_alias_resolve / dshe_canonical_resolve / gate_full_run / migration_verify
    version_tag           TEXT NOT NULL,
    priority              INT NOT NULL DEFAULT 5,  -- 1(最高)..10(最低)
    submitter             TEXT NOT NULL,
    payload               JSONB NOT NULL,         -- 任务参数
    status                TEXT NOT NULL DEFAULT 'queued',  -- queued / running / succeeded / failed / cancelled / timeout
    progress              NUMERIC(4,2) DEFAULT 0.00,
    progress_msg          TEXT,
    worker_id             TEXT,                    -- 认领该任务的 worker
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enqueued_at           TIMESTAMPTZ,
    started_at            TIMESTAMPTZ,
    finished_at           TIMESTAMPTZ,
    result_ref            TEXT,                    -- 指向 result_store 的键
    error                 TEXT,
    retry_count           INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_status CHECK (status IN ('queued','running','succeeded','failed','cancelled','timeout'))
);
CREATE INDEX idx_task_status ON task_run(status, enqueued_at);
CREATE INDEX idx_task_type ON task_run(task_type, created_at DESC);
```

### 3.4 审计域

#### `audit_log`（写入审计，不可变追加）
```sql
CREATE TABLE audit_log (
    id                    BIGSERIAL PRIMARY KEY,
    ts                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor                 TEXT,                   -- user / service_account / agent
    action                TEXT NOT NULL,          -- alias.create / rule.update / gate_run.start / ...
    target_type           TEXT,                   -- alias / rule / gate_run / task
    target_id             TEXT,
    version_tag           TEXT,
    before_snapshot       JSONB,
    after_snapshot        JSONB,
    ip_address            INET,
    request_id            TEXT
);
CREATE INDEX idx_audit_ts ON audit_log(ts DESC);
CREATE INDEX idx_audit_target ON audit_log(target_type, target_id);
```

### 3.5 配置域

#### `config_snapshot`（Gate 配置、引擎配置快照）
```sql
CREATE TABLE config_snapshot (
    id                    BIGSERIAL PRIMARY KEY,
    config_kind           TEXT NOT NULL,          -- gate_config / engine_config / blacklist_snapshot
    version               INT NOT NULL,
    payload               JSONB NOT NULL,
    md5                   CHAR(32) NOT NULL,      -- 与磁盘文件 MD5 对齐
    source_file           TEXT,
    activated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (config_kind, version),
    UNIQUE (config_kind, md5)
);
```

**说明**：Gate 配置和黑名单文件的 MD5 强制对齐磁盘文件，避免"注册表说 v3 但磁盘还是 v2"的漂移。

---

## 4. 关键设计决策

### 4.1 为什么保留 CSV 别名库作为迁移源

- `indicator_alias_library.csv` 是 V85 冻结基线；V86 引擎必须能读回旧数据做兼容性验证
- DB 表 `alias_mapping` 通过 `v85_alias_id` / `v85_confidence` 字段建立双向映射
- 迁移脚本 `migrate_alias_v85_to_v86.py`（不在本任务交付物内）负责灌库

### 4.2 为什么规则用 JSONB 而不是强类型字段

- 3 种规则类型（blacklist/fuzzy/gate）字段结构差异大
- JSONB + 索引可以兼顾灵活查询和结构化存储
- 但顶层字段（`rule_id`, `status`, `severity`）保持强类型，避免"全 JSONB"的失控

### 4.3 为什么 Gate 结果按 (run_id, gate_id) 唯一

- 一次 run 每项 Gate 只记录一次最终裁决
- 详细用例级数据放 `detail` JSONB（如 G4 的 18 个边界样例结果）
- 需要历史对比时按 `gate_id` + `verdict` 索引扫

### 4.4 为什么 MD5 与磁盘文件绑定

- V85 已证明：磁盘文件被 `core.autocrlf=true` 转换 CRLF→LF 后 MD5 与 git blob 不同
- V86 强制在 `config_snapshot.md5` 里对齐磁盘实际 MD5，避免"我提交的是版本 X 但服务读到版本 Y"的漂移
- 每次 Gate 运行必须引用 `config_snapshot.id`，可回放

### 4.5 为什么审计独立成表

- V85 冻结后不允许改任何业务结果
- V86 引入写入后必须有独立审计链路
- `audit_log` 独立于业务表，可跨库归档到冷备

### 4.6 为什么任务表和 Gate 表分开

- `task_run` 是异步任务调度（提交→认领→执行→回写），生命周期由 worker 驱动
- `gate_run` 是同步批量运行（一次触发、并行 14 项 Gate、同步返回），生命周期由 run 触发器驱动
- 一个 task_run 可以触发多个 gate_run（例如一次 DSHE 解析任务触发 G1/G2/G3/G4 四项回归）

---

## 5. 索引策略

| 表 | 索引 | 用途 |
|---|---|---|
| alias_mapping | `(alias_norm)` / `(canonical_key, canonical_name)` / `(status, variety_family)` | 别名查询、规范反查、按状态过滤 |
| alias_variant | `(alias_id)` | 查某 alias 下所有形态 |
| alias_source | `(alias_id)` | 查某 alias 的所有源引用 |
| rule_version | `(rule_id, activated_at DESC)` | 查某规则的生效版本链 |
| gate_run | `(version_tag, started_at DESC)` | 按版本列出运行 |
| gate_result | `(run_id)` / `(gate_id, verdict)` | 单 run 复盘 / 全历史 Gate 通过率 |
| task_run | `(status, enqueued_at)` | Worker 认领队列 |
| audit_log | `(ts DESC)` / `(target_type, target_id)` | 时间线 / 对象追溯 |

---

## 6. 与 V85 只读接口的对应关系

| V85 制品（只读） | V86 目标表 | 迁移方式 |
|---|---|---|
| `alias_library`（CSV） | `alias_mapping` + `alias_variant` + `alias_source` | 一次性灌库 |
| `multi_canonical_conflicts`（CSV） | `alias_mapping` 中 `relation=canonical_conflict` | 优先灌库，供 F2 择优 |
| `alias_test_case_set`（JSON） | 不入 DB（保留磁盘 JSON，作为回归测试基线） | 引用不复制 |
| `blacklist_v85_final`（JSON） | `rule_registry` + `rule_version`（rule_kind='blacklist'） | 一次性灌库 |
| `gate_config`（JSON） | `config_snapshot`（config_kind='gate_config'） | 一次性灌库 + MD5 绑定 |
| `risk_db`（CSV） | 保留 CSV，V86 通过只读接口查询（不复制进 DB） | 引用不复制 |
| `chart_risk_bound`（JSON） | 保留 JSON，V86 通过只读接口查询 | 引用不复制 |

**核心原则**：V86 DB 只存"版本化可演进"的数据（别名/规则/配置/运行/审计），不复制"冻结快照"数据（风险库/图表绑定）。冻结数据始终走只读接口。

---

## 7. 迁移脚本草图（伪代码，非交付物）

```python
def migrate_alias_library_v85_to_v86():
    api = ArtifactAPI(repo_root="D:/DSH_WORK/framework-tree", token="v85-portal-r-0001")
    # 1) 校验源文件
    meta = api.get_artifact_meta("alias_library", version="f313570")
    assert meta["md5"] == EXPECTED_MD5, f"alias_library 校验失败"
    # 2) 分页读取
    rows = api.query("alias_library", limit=10000, offset=0)["rows"]
    # 3) 逐条写入 alias_mapping
    with db.connect() as conn:
        for row in rows:
            norm = normalize(row["alias_name"])
            conn.execute("""
                INSERT INTO alias_mapping
                (alias_norm, canonical_key, canonical_name, variety_family,
                 alias_type, relation, confidence, status, alias_id, v85_alias_id, v85_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                ON CONFLICT (alias_norm, canonical_key) DO NOTHING
            """, (norm, canonical_key, canonical_name, variety_family,
                  row["alias_type"], "cross_pair", row["similarity_score"]/100.0,
                  f"A-{...}", row["alias_id"], row["similarity_score"]/100.0))
```

---

## 8. 未来扩展点

| 扩展方向 | 现状 | 保留口子 |
|---|---|---|
| 多租户 | 不支持 | `tenant_id` 字段未在表内定义，未来需全表迁移 |
| 别名置信度在线学习 | 无 | `alias_mapping.confidence` 保留 NUMERIC，可扩展学习更新 |
| 规则热更新 | 无（版本化+激活） | `rule_version.activated_at` 支持时间线切换 |
| Gate 结果可视化 | 无 | `gate_result.detail` JSONB 保留原始用例数据 |
| 任务优先级队列 | 简单 int | `priority` + `enqueued_at` 组合索引 |
| 冷备归档 | 无 | `task_run` 表 90 天后归档到 Parquet |

---

## 9. 依赖声明

| 依赖 | 状态 | 影响 |
|---|---|---|
| `v86_init_backlog_total.md` | **未就绪**（HERMES 产出） | 表设计不受影响；未来若 backlog 引入新表需求，走 `ADD COLUMN` / `CREATE TABLE` 增量迁移 |
| `v85_version_freeze_decision.md` | **未就绪**（HERMES 产出） | 版本锁定策略沿用 V85 现状（`f313570` 冻结）；未来若 freeze_decision 引入更细粒度锁定，扩展 `config_snapshot` |
| V85 只读接口 | 已交付（同目录 `v85_artifact_api.py`） | 迁移脚本通过只读接口读取 V85 数据，不直接访问文件系统 |

---

## 10. 约束合规

- ✅ 不修改 V85 冻结数据（`NO_MODIFY_SOURCE=TRUE` / `NO_GT_MODIFICATION=TRUE`）
- ✅ 不调用 zhiji API（`NO_ZHIJI_API_CALL=TRUE`）
- ✅ 不生成业务结果（本设计仅定义存储结构，不执行任何数据写入）
- ✅ 分支锁定 `feature/v85-chart-template`
- ✅ 只新增设计文档，不覆盖任何既有产物
