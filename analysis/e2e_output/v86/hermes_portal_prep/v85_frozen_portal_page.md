# V85 冻结版本评审门户固化页面（v7-frozen）

> 工单: `HERMES_V86_PORTAL_INTEGRATE_AND_V85_FROZEN_DEMO_LOCK` · T2.1 + T2.2
> 生成时间: 2026-10-02 09:30
> 分支: `feature/v85-chart-template`
> 基线门户: `enhanced_review_portal_v6_final_refreshed.md`（commit `a2815c4`）
> 数据源: E `v85_artifact_api.py` 只读 API（commit `b7c62ba`）
> 快照: B `da2a440` / git tag `v85-final-persist`

---

## 1. 版本标签展示（门户顶部强制横幅）

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🔒 V85.0 FROZEN                                                          │
│ version_tag: v85.0   commit: f313570   tag: v85-final-persist @ da2a440 │
│ branch: feature/v85-chart-template   frozen_at: 2026-10-01              │
│ 31 规则 / 864 别名 / 50 风险 / 488 模板 / 31 制品已登记                  │
│ ⚠️ 本环境为只读演示环境，所有编辑功能已禁用，数据由冻结快照提供          │
└─────────────────────────────────────────────────────────────────────────┘
```

实现要求：横幅高度 64px、背景 `#7f1d1d`（红）、白色字体、不可折叠、置顶 fixed。

---

## 2. 数据源改造：本地文件读取 → 只读 API

### 2.1 数据层职责迁移

| 项 | V6 门户（改造前） | V7-frozen（改造后） |
|---|---|---|
| 风险库 | 本地 CSV 直读 | `GET /artifacts/risk_db/query` |
| 场景回放 | 本地 CSV 直读 | `GET /artifacts/scenario_replay/query` |
| 黑名单 | 本地 JSON 直读 | `GET /artifacts/blacklist_v85_final/file` |
| 别名库 | 本地 CSV 直读 | `GET /artifacts/alias_library/query` |
| 混淆对 | 本地 CSV 直读 | `GET /artifacts/high_risk_confusion_pairs/query` |
| 风险边界 | 本地 JSON 直读 | `GET /artifacts/chart_risk_bound/file` |
| 跨品种 P0 | 本地 CSV 直读 | `GET /artifacts/cross_variety_p0/query` |
| 渲染清单 | 本地 JSON 直读 | `GET /artifacts/template_manifest/file` |
| 制品清单 | 无（硬编码） | `GET /artifacts`（动态 31 项） |
| MD5 校验 | 无 | `GET /artifacts/{kind}/verify` |

**门户不再持有任何本地业务数据副本**；所有数值来自 API 响应，禁止前端落盘。

### 2.2 数据访问适配层（`v85_portal_data_client.py`）

```python
from v85_artifact_api import ArtifactAPI, ApiError

class PortalReadOnlyClient:
    """V85 冻结门户数据访问层 — 单例，进程内直连，无 HTTP 开销。"""
    TOKEN = "v85-portal-r-0001"   # portal_read 角色
    VERSION = "f313570"
    _instance = None

    def __new__(cls, repo_root=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._api = ArtifactAPI(repo_root=repo_root, token=cls.TOKEN)
        return cls._instance

    # --- 版本与探活 ---
    def health(self):
        return self._api.health()

    def versions(self, include_inactive=False):
        return self._api.list_versions(include_inactive=include_inactive)

    def artifacts_catalog(self):
        return self._api.list_artifacts(version=self.VERSION)

    # --- 业务查询（替代本地文件读取）---
    def risk_db(self, filters=None, limit=10000):
        return self._api.query("risk_db", version=self.VERSION,
                               filters=filters, limit=limit)

    def scenario_replay(self, filters=None, limit=10000):
        return self._api.query("scenario_replay", version=self.VERSION,
                               filters=filters, limit=limit)

    def alias_library(self, filters=None, limit=10000):
        return self._api.query("alias_library", version=self.VERSION,
                               filters=filters, limit=limit)

    def confusion_pairs(self, filters=None, limit=10000):
        return self._api.query("high_risk_confusion_pairs", version=self.VERSION,
                               filters=filters, limit=limit)

    def cross_variety_p0(self, filters=None, limit=10000):
        return self._api.query("cross_variety_p0", version=self.VERSION,
                               filters=filters, limit=limit)

    # --- 整文件（小文件 ≤256KiB）---
    def blacklist(self):
        return self._api.get_file("blacklist_v85_final", version=self.VERSION)

    def risk_boundary(self):
        return self._api.get_file("chart_risk_bound", version=self.VERSION)

    def template_manifest(self):
        return self._api.get_file("template_manifest", version=self.VERSION)

    # --- MD5 快照校验（快照面板专用）---
    def verify_artifact(self, kind, expected_md5, verify_file=True):
        return self._api.verify_artifact_md5(
            kind, version=self.VERSION, expected_md5=expected_md5,
            verify_file=verify_file)
```

### 2.3 关键调用示例

```python
client = PortalReadOnlyClient(repo_root="/home/ubuntu/framework-tree")

# 1) 探活 + 版本校验（门户启动第一步）
h = client.health()
assert h["read_only"] is True and h["registered_artifacts"] == 31
v = client.versions()
frozen = [x for x in v["versions"] if x["readable"]][0]
assert frozen["key"] == "f313570" and frozen["version_tag"] == "v85.0"

# 2) P0 拦截率面板
q = client.risk_db(filters={"risk_level": "P0"})
p0_total = q["filtered"]

# 3) 冻结完整性：快照 MD5 校验
snap = load_snapshot_manifest()   # 来自 B da2a440 持久快照
for row in snap["artifacts"]:
    r = client.verify_artifact(row["kind"], row["md5"], verify_file=True)
    assert r["match"], f'{row["kind"]} 快照不一致: {r}'
```

### 2.4 降级与容错

| 故障 | 门户行为 |
|------|---------|
| API 不可达 | 全屏 `🔴 数据源不可用`，禁止展示任何缓存数字 |
| 版本 `readable=False` | 展示版本名 + `403 VERSION_READ_FORBIDDEN` 说明 |
| MD5 校验失败 | 该制品面板标红，顶部横幅追加 `⚠️ 快照校验失败` |
| 响应 > 256 KiB | 自动切换 `/query` 分页（`limit=100`） |

---

## 3. 快照 MD5 校验面板（新增 Tab）

**Tab 标签**：`🔐 快照校验`

| 字段 | 内容 |
|------|------|
| 快照来源 | `B_V85_ARTIFACT_PERSIST_AND_SNAPSHOT_VERIFY` @ `da2a440` |
| Git tag | `v85-final-persist` |
| 快照范围 | 453 文件（MD5 100% / 结构 100% / 解析 99.1% / 只读 100%） |
| API 制品 | 31 项已登记 |

### 3.1 面板表头

| 制品 kind | relpath | 快照 MD5 | API 实时 MD5 | 校验 |
|---|---|---|---|---|
| risk_db | unified_risk_db/unified_indicator_risk_db.csv | `819cb85a…` | 实时重算 | ✅/❌ |
| …（31 项全量） | | | | |

### 3.2 交互

1. 点击「全量校验」→ 顺序调用 `verify_artifact(kind, snap_md5, verify_file=1)`
2. 每项 100ms 节流，31 项全量约 3.1 秒
3. 单行 ❌ → 行标红 + 顶部横幅告警 + 记录 `AUDIT_VERIFY_FAIL`
4. 汇总卡：`通过 31/31` 绿色；任一失败 → `通过 N/31` 红色并禁止进入其他 Tab

### 3.3 校验结果持久化

校验结果仅存于浏览器 sessionStorage，刷新页面即清除，**不落盘、不上传**（保持 V85 只读）。

---

## 4. 演示环境锁定

### 4.1 禁止修改项

| 项 | 状态 | 说明 |
|---|---|---|
| 评审状态回写 | 🔒 禁用 | V6 的 `review_result_apply.py` 入口已移除 |
| 白名单追加 | 🔒 禁用 | 需走 V86 任务接口 |
| THS zhiji_id 回写 | 🔒 禁用 | 需走 V86 任务接口 |
| 黑名单编辑 | 🔒 禁用 | V85 31 规则冻结 |
| 别名库编辑 | 🔒 禁用 | V85 864 条冻结 |
| 批量导出导入 | 🔒 禁用 | 仅保留导出（只读） |

### 4.2 演示专用保留项

| 项 | 状态 | 说明 |
|---|---|---|
| 场景 A/B 切换 | ✅ 保留 | 仅切换 API 查询参数 |
| 批次 A/B/C 浏览 | ✅ 保留 | 只读展示评审批次数据 |
| Gate 大盘 | ✅ 保留 | 52 项 Gate 只读展示 |
| 风险筛选/搜索 | ✅ 保留 | 前端过滤 API 返回结果 |

---

## 5. 操作手册

### 5.1 启动

```bash
# 1) 环境自检（6 项）
python3 scripts/bootstrap_agent.sh

# 2) 启动 API 进程自检
python3 analysis/e2e_output/v85/e_api_design/v85_artifact_api.py --smoke

# 3) 启动门户（本地预览）
python3 -m http.server 8766
# 访问 http://124.221.113.37:8766/nickel-gh/
```

### 5.2 门户使用流程

1. 打开门户 → 顶部横幅显示 🔒 V85.0 FROZEN
2. 点击「🔐 快照校验」→ 「全量校验」→ 等待 `通过 31/31`
3. 校验通过后方可使用其他 Tab
4. 切换「场景 A / 场景 B」查看 P0 拦截率对比
5. 「📊 指标大盘」查看 52 项 Gate + P0/TP/FP
6. 「📄 制品目录」浏览 31 项制品（含 relpath / MD5 / 字节数）

### 5.3 常见故障

| 症状 | 原因 | 处理 |
|------|------|------|
| 横幅显示 🔴 | API 进程未启动 | 跑 `v85_artifact_api.py --smoke` |
| 快照校验 ❌ | 工作区有未提交改动 | `git status` 检查，`git checkout -- <file>` |
| `VERSION_READ_FORBIDDEN` | 请求了 v86-dev | 版本参数固定 `f313570` |
| 数字与 V6 不一致 | 正常，V6 是本地副本 | 以 API 为准 |

### 5.4 只读声明

本门户为 **FROZEN READ-ONLY** 演示环境：

- 所有数据通过 `v85_artifact_api.py` 只读 API 提供
- API 三重写保护：HTTP 层 405 / API 层 403 / 版本层 `VERSION_WRITABLE`
- 前端不持有任何本地业务数据副本
- 门户不发起 zhiji API 调用（`NO_ZHIJI_API_CALL=TRUE`）
- 门户不修改 V85 任何原始计算结果
