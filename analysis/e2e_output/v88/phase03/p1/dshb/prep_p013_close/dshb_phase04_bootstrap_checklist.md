# V88 Phase04 — DSHB 数据侧 Bootstrap 初始化清单

> **TASK_ID**: V88_PHASE03_P1_DSHB_PREP_P013_CLOSE_JOB (T4)
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **生成日期**: 2026-10-24
> **文档目的**: 确保 Phase03→Phase04 数据基础设施无缝过渡
> **前置**: V88 Phase03 P1 完成 (P0-9修复 / 爬虫LIVE验证 / 噪声观测进行中)
> **Phase04 规划**: 36项新指标 / 8品种 (CU/AL/ZN/NI/SN/SI/LI + AU/AG) / 59.5人天 / 13周
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY

---

## 0. 约束合规声明 (Constraints Compliance)

| 约束 | 状态 | 证据 |
|------|:----:|------|
| BRANCH_LOCKED | ✅ feature/v88-g1 | 仅写入 `prep_p013_close/`，未修改其他分支文件 |
| NO_OVERWRITE | ✅ | 新建文档，不覆盖任何既有文件 |
| NO_MODIFY_V87 | ✅ | 未触及 V87 基线数据/规则 |
| NO_EDIT_RELEASE_TAG | ✅ | 未修改任何发布标签 |
| NO_ZHIJI_API_CALL | ✅ | 0 calls（检查清单设计阶段，无外部调用） |
| APPEND_ONLY | ✅ | 仅追加新文件 |
| UPSTREAM_WRITES=0 | ✅ | 未修改 `scripts/dqa/`、`scripts/`、`data/`、`STATUS.md` |
| PRE_COMMIT_HOOK | ✅ N/A | 未改产物文件（*.html/*.py/*.js/data/*.json） |

---

## 1. 检查清单概述 (Checklist Overview)

### 1.1 目的

本清单旨在为 **V88 Phase04** 数据侧提供一份完整的初始化检查框架，确保：
- Phase03 交付物（数据/爬虫/DQA/基线）可追溯、可复用
- P0-13 噪声基线在 Phase04 启动前完成 168h 观测
- P0-12 CPU 基线已达标（DSHE v1.4.0-cpu-triple-fix，EXEMPTION_GRANTED）
- 36项新指标的数据源/爬虫/DQA规则准备就绪
- 环境与配置满足 Phase04 开发要求

### 1.2 适用范围

| 范围 | 说明 |
|------|------|
| 数据基础设施 | 数据库/目录/文件权限/API密钥/配置 |
| 爬虫 | SPOT_IS v2 / SMM Cloudflare bypass / 36指标爬虫 |
| 数据质量 | DQA-01~08 (已有) + DQA-09~15 (新增) |
| 存储与监控 | 阈值基线 / 噪声率 / CPU 基线 |
| 开发环境 | 环境变量/服务账号/CI/CD |

### 1.3 工作量估算

| 阶段 | 人天 | 周次 |
|------|:----:|:----:|
| 环境设置 + 数据管道 | 5.0 | W1-2 |
| 爬虫开发 + 测试 | 18.0 | W3-5 |
| DQA规则生产部署 | 6.5 | W6-8 |
| 集成测试 + 性能调优 | 10.0 | W9-11 |
| 最终验证 + 交接 | 4.0 | W12-13 |
| 风险缓解 + 数据回填 | 12.5 | 贯穿 |
| 缓冲 | 3.5 | 贯穿 |
| **总计** | **59.5** | **13周** |

### 1.4 Phase04 品种覆盖

| 品种代码 | 名称 | 指标数 | 板块 |
|:--------:|------|:------:|------|
| CU | 铜 | 6 | 价格/库存/供给/需求/成本/衍生品 |
| AL | 铝 | 6 | 价格/库存/供给/需求/成本/衍生品 |
| ZN | 锌 | 4 | 价格/库存/供给/需求 |
| NI | 镍 | 4 | 价格/库存/供给/需求 |
| SN | 锡 | 4 | 价格/库存/供给/需求 |
| SI | 硅 | 4 | 价格/库存/供给/衍生品 |
| LI | 锂 | 4 | 价格/库存/需求/衍生品 |
| AU | 金 | 2 | 价格/库存 |
| AG | 银 | 2 | 价格/库存 |
| **合计** | **9品种** | **36** | — |

---

## 2. 数据环境检查清单 (Data Environment Checklist)

### 2.1 数据库状态验证

- [ ] **phase03_test.db 完整性** — 总行数 590,455 / 指标数 718 / 主键冲突 0 / 导入错误 0
- [ ] **表结构确认** — `series_cache` (date/value) + `indicator_meta` (元数据) 双表可用
- [ ] **数据日期范围** — 覆盖 2015-01-02 ~ 2026-10-15 (含 Phase03 P1 全部派生指标)
- [ ] **品种覆盖** — 12品种: cu/al/pb/zn/ni/sn/si/li/au/ag/wr/other
- [ ] **已映射指标** — 709/718 = 98.7% (indicator_id_mapped 非空)
- [ ] **未映射指标** — 9项 placeholder 已标记 (COMEX_AL/COMEX_NI/COMEX_PB/COMEX_SN/COMEX_ZN/CU_BALANCE_SHEET/PB_TOP20_LONG/PB_TOP20_SHORT/SPOT_IS)
- [ ] **派生指标** — 70项已入库 (59项P1 + 11项P0-9FIX补齐)
- [ ] **备份与恢复** — phase03_test.db 完整备份已执行，恢复演练通过

### 2.2 目录结构就绪

- [ ] `analysis/e2e_output/v88/phase03/p1/dshb/` — Phase03 交付物归档完成
- [ ] `analysis/e2e_output/v88/phase04/` — Phase04 工作目录已创建
- [ ] `analysis/e2e_output/v88/phase04/dshb/` — DSHB 数据侧工作目录就绪
- [ ] `scripts/dqa/` — DQA规则目录 (Phase04 新增 DQA-09~15)
- [ ] `scripts/dqa/rules/` — 规则实装子目录
- [ ] `scripts/crawler/` — 爬虫脚本目录
- [ ] `scripts/crawler/logs/` — 爬虫运行日志
- [ ] `scripts/crawler/external_raw/` — 爬虫原始数据缓存
- [ ] `data/` — 数据文件目录 (Phase04 新增 JSONL 导出)
- [ ] `data/db_export/` — 数据库导出子目录

### 2.3 文件权限与访问控制

- [ ] 仓库写权限: DSHB agent 对 `analysis/` 目录有完整写权限
- [ ] 分支保护: feature/v88-g1 BRANCH_LOCKED，禁止直接 push 到 main
- [ ] 文件锁机制: 写文件前执行 `file_write_lock.py acquire`
- [ ] 只读文件: phase03_test.db (不修改，仅读取用于基线对比)
- [ ] Git hooks 安装: `git config core.hooksPath scripts/hooks` 已配置
- [ ] Pre-commit 检查: 改产物文件必须同步更新 STATUS.md

### 2.4 API 密钥管理

- [ ] **知几 API** — 配额已恢复，`zhiji_api.py` search/series 正常返回
  - [ ] API key 存储在 `~/.hermes/scripts/zhiji_api.py` (不进仓库)
  - [ ] 配额监控: 每日检查 `bootstrap_agent.sh` 配额探测
  - [ ] 限频策略: 1秒限频，写入 `api_cache.db`
- [ ] **Wind 授权** — 目标签约日期 2026-11-07 (R-V88-042)
  - [ ] Wind API Token 申请 (C05)
  - [ ] Wind终端安装至目标服务器 (C06)
  - [ ] API 连通性测试 (C07)
  - [ ] 数据样本验证 (C08)
  - [ ] 预算审批 ~¥20,000/年 (C10)
  - [ ] 数据范围协议签署 (C12)
- [ ] **SMM API** — 上海有色网授权确认
  - [ ] SMM 数据范围 (铜/铝加工费 TC/RC)
  - [ ] SMM 反爬规避方案就绪 (Cloudflare bypass 原型已验证)
- [ ] **SHFE** — 上海期货交易所数据访问
  - [ ] 交易所库存数据 API 权限确认
  - [ ] Top20 持仓数据 (需 Wind 或 SHFE 授权)
- [ ] **海关总署** — 进口量数据
  - [ ] 铜/铝进口量数据授权确认
- [ ] **统计局** — 铅酸电池产量数据
  - [ ] 统计局 API 访问确认

### 2.5 配置文件

- [ ] **爬虫配置** — `crawler_config.yaml` 已更新 (含 SPOT_IS v2 5项URL修复)
- [ ] **DQA 配置** — `dqa_config.yaml` 已扩展 (含 DQA-09~15 新规则定义)
- [ ] **阈值配置** — `threshold_config.yaml` 已更新 (三级阈值: 正常/预警/熔断)
  - 正常区间: P10 ~ P90
  - 预警区间: P05~P10 或 P90~P95
  - 熔断区间: < P05 或 > P95
- [ ] **降级配置** — `degrade_config.yaml` 已配置 8 BLOCKED 降级逻辑
- [ ] **交易日历** — `trading_calendar.json` 已准备 (DQA-15 日历豁免需要)
- [ ] **指标注册表** — `indicator_registry.json` 已扩展 36项新指标
- [ ] **数据源映射表** — `data_source_mapping.json` 已准备 (36指标 × 数据源)
- [ ] **依赖DAG** — `indicator_dependency_dag.json` 已准备 (DQA-14 需要)

### 2.6 日志与监控基础设施

- [ ] **爬虫日志** — `scripts/crawler/logs/` 目录就绪，含结构化 JSONL 输出
- [ ] **DQA 日志** — `scripts/dqa/logs/` 目录就绪，含规则执行日志
- [ ] **噪声观测日志** — `noise_7d_log.jsonl` 连续观测中 (PID 32672)
- [ ] **告警通道** — ALERT-04 (Crawl Failed) / ALERT-05 (DQA Fail) 告警配置
- [ ] **监控仪表盘** — 噪声率/CPU/爬虫成功率实时监控面板就绪
- [ ] **日志轮转** — 日志轮转策略配置 (保留7天，压缩归档)

---

## 3. 前置数据集 (Pre-Requisite Datasets)

### 3.1 P0-13 噪声基线

| 项目 | 值 |
|------|-----|
| 状态 | ⏳ **PENDING** — 168h 观测窗口进行中 (88.1% 完成) |
| 进程 PID | 32672 |
| 启动时间 | 2026-10-15T16:39:20 |
| 预计完成时间 | 2026-10-22T16:39:20 |
| 当前噪声率 | **7.54%** (< 10% 阈值) |
| 安全裕度 | 2.46pp |
| 观测进度 | 88.1% (148h / 168h) |
| 总数据点 | 589,272 |
| 总噪声点 | 44,430 |
| 达标指标 | 623/717 (86.9%) |
| 交付物 | `noise_7d_log.jsonl` + `v88_phase03_p1_noise_7d_summary.md` |

- [ ] 等待 168h 观测窗口完成 (预计 2026-10-22)
- [ ] 生成 `v88_phase03_p1_noise_7d_summary.md` 总结报告
- [ ] P0-13 门禁判定: 7天静默期噪声率 < 10% → **PASS**
- [ ] 更新风险台账 R-V88-035 状态 → CLOSED
- [ ] HERMEShf 审计确认

### 3.2 P0-12 渲染 CPU 基线

| 项目 | 值 |
|------|-----|
| 状态 | ✅ **DONE** — DSHE v1.4.0-cpu-triple-fix |
| cpu_peak_pct | 0.0654% (远低于 2.0% 熔断阈值) |
| 原生测试 | PASS |
| 版本 | v1.4.0-cpu-triple-fix |
| HERMES 审批 | ✅ EXEMPTION_GRANTED |
| 关联风险 | R-V88-034 (OPEN → MITIGATED, 豁免已授予) |

- [ ] P0-12 门禁已关闭 (HERMES 豁免审批)
- [ ] DSHE CPU 基线文档已归档 (`p0_10_cpu_optimization_compare.json`)
- [ ] R-V88-034 风险状态更新为 MITIGATED (豁免)

### 3.3 36指标数据源注册表

| 批次 | 指标数 | 数据源 | 状态 |
|:----:|:------:|--------|:----:|
| 价格信号 (6) | 6 | 知几API | ✅ 已有数据源 |
| 库存动态 (6) | 6 | 知几API + SHFE | ⚠️ 部分需补充 |
| 供给指标 (6) | 6 | 工业协会 + 海关 | 🔴 需新增爬虫 |
| 需求指标 (6) | 6 | 知几API + 统计局 | ⚠️ 需优化 |
| 成本利润 (6) | 6 | SMM + 代理计算 | 🔴 需新增爬虫 |
| 衍生品 (6) | 6 | SHFE + COMEX (派生) | ⚠️ 需优化 |

- [ ] 36项指标数据源注册表已生成 (`data_source_mapping.json`)
- [ ] 已知数据源覆盖: 22项 (61.1%) 完全匹配
- [ ] 需补充数据源: 10项 (27.8%) 部分匹配
- [ ] 需新建数据源: 4项 (11.1%) 无匹配

### 3.4 Wind 数据授权验证

- [ ] Wind 商务审批流程启动 (C01) — 待启动
- [ ] Wind 合同模板确认 (C02) — 待获取
- [ ] 数据范围协议确认 (C03) — ✅ 已确认
- [ ] 数据使用条款合规 (C04) — ✅ 已审核
- [ ] Wind API Token 申请 (C05) — 截止 2026-11-03
- [ ] Wind 终端安装 (C06) — 截止 2026-10-31
- [ ] Wind API 连通测试 (C07) — 截止 2026-11-03
- [ ] 数据样本验证 (C08) — 截止 2026-11-05
- [ ] Schema 兼容性验证 (C09) — ✅ 已完成
- [ ] 预算审批 ~¥20,000/年 (C10) — 截止 2026-10-25
- [ ] DSHE 集成团队排期 (C11) — 截止 2026-10-28
- [ ] 数据范围协议签署 (C12) — 目标 2026-11-07

### 3.5 爬虫数据质量基线

- [ ] SPOT_IS 爬虫 v2 (5项URL修复) — ✅ 7/7 TC PASS
- [ ] SMM Cloudflare bypass 原型 (765行) — ✅ 4层重试策略验证通过
- [ ] COMEX 日度爬虫 — ✅ 正常运作
- [ ] LC_FU 爬虫 — ✅ 正常运作
- [ ] 爬虫调度器 — ✅ 正常运作
- [ ] 爬虫 DQA 检查 — ✅ 8/8 规则通过
- [ ] 爬虫降级逻辑 (8 BLOCKED) — ✅ 降级配置就绪

---

## 4. 爬虫基础设施检查清单 (Crawler Infrastructure Checklist)

### 4.1 SPOT_IS 爬虫 v2 部署

| 项目 | 值 |
|------|-----|
| 爬虫版本 | v88-p1-t2-spot-is-mvp-v1.0 |
| 数据源 | 100ppi.com (生意社) |
| 指标 | SPOT_IS (工业硅现货价格) |
| URL 修复数 | 5项 |
| 测试结果 | 7/7 TC PASS |
| LIVE 模式 | ✅ 正常 |

- [ ] SPOT_IS v2 爬虫脚本已部署 (`spot_is_crawler.py`)
- [ ] 5项 URL 修复已验证通过
- [ ] DRY-RUN 测试 7/7 轮通过
- [ ] LIVE 测试通过 (非404)
- [ ] 爬虫 DQA 检查通过
- [ ] 爬虫调度器集成完成

### 4.2 SMM Cloudflare Bypass 原型

| 项目 | 值 |
|------|-----|
| 爬虫 | `cu_balance_sheet_crawler.py` |
| 指标 | CU_BALANCE_SHEET (铜资产负债表) |
| 数据源 | SMM + ICSG |
| 原型代码 | 765行 |
| 重试策略 | 4层 (重试/延迟/代理/降级) |
| 验证状态 | ✅ 原型验证通过 |

- [ ] SMM Cloudflare bypass 原型已验证 (765行)
- [ ] 4层重试策略已实现并测试:
  - Layer 1: 指数退避重试 (最多3次)
  - Layer 2: 随机延迟间隔 (1-5秒)
  - Layer 3: 代理IP轮换 (备用代理池)
  - Layer 4: 降级到模拟数据
- [ ] ICSG 主源超时处理 (Geo-block 缓解)
- [ ] SMM fallback 源 Cloudflare 绕过验证
- [ ] DRY-RUN 5/6 轮通过 (83.3%)，BUG-BS-001 已修复

### 4.3 DQA-09~15 规则激活

| 规则 | 名称 | 复杂度 | 工时 | 状态 |
|:----:|------|:------:|:----:|:----:|
| DQA-09 | 数据源交叉验证 | M | 1.0d | 🔴 待实装 |
| DQA-10 | 代理估算置信度 | M-H | 1.2d | 🔴 待实装 |
| DQA-11 | 月度/日度频率一致性 | M | 0.8d | 🔴 待实装 |
| DQA-12 | 源时滞检测 | L | 0.5d | 🔴 待实装 |
| DQA-13 | 历史覆盖率 | L | 0.4d | 🔴 待实装 |
| DQA-14 | 依赖链一致性 | M-H | 1.3d | 🔴 待实装 |
| DQA-15 | 日历豁免 | M | 0.8d | 🔴 待实装 |
| 单元测试+集成 | — | — | 0.5d | 🔴 待实装 |
| **合计** | | | **6.5d** | — |

- [ ] DQA-09 数据源交叉验证规则实装
- [ ] DQA-10 代理估算置信度规则实装 (置信区间 < 95% 告警)
- [ ] DQA-11 月度/日度频率一致性规则实装 (日度插值一致性)
- [ ] DQA-12 源时滞检测规则实装
- [ ] DQA-13 历史覆盖率规则实装 (36指标基线)
- [ ] DQA-14 依赖链一致性规则实装 (依赖DAG)
- [ ] DQA-15 日历豁免规则实装 (交易日历库)
- [ ] 全部7条规则单元测试通过
- [ ] 全部7条规则集成测试通过 (36指标全量管道)
- [ ] DQA-09~15 集成至 CI/CD 管道
- [ ] DQA-09~15 集成至 `verify_testdb.py` 校验脚本

### 4.4 8 BLOCKED 降级逻辑集成

| BLOCKED 项 | 类型 | 降级方案 | 状态 |
|------------|------|----------|:----:|
| BLOCKED-01 | 月度供给 (CU) | 代理估算 + 月度插值 | 🔴 待集成 |
| BLOCKED-02 | 月度供给 (AL) | 代理估算 + 月度插值 | 🔴 待集成 |
| BLOCKED-03 | 月度供给 (ZN) | 代理估算 + 月度插值 | 🔴 待集成 |
| BLOCKED-04 | 月度供给 (NI) | 代理估算 + 月度插值 | 🔴 待集成 |
| BLOCKED-05 | 开工率 (CU) | 代理估算模型 | 🔴 待集成 |
| BLOCKED-06 | 开工率 (AL) | 代理估算模型 | 🔴 待集成 |
| BLOCKED-07 | 冶炼利润 (CU) | 价格+加工费推导 | 🔴 待集成 |
| BLOCKED-08 | 冶炼利润 (AL) | 价格+加工费推导 | 🔴 待集成 |

- [ ] 8项 BLOCKED 降级逻辑全部实装
- [ ] 降级触发条件: 爬虫失败 / 数据源不可用 / DQA FAIL
- [ ] 降级数据标记: `source='degraded'` + `degrade_reason` 字段
- [ ] 降级数据质量: DQA-10 代理置信度 < 95% 告警
- [ ] 降级恢复条件: 原始数据源恢复后自动切换
- [ ] 降级监控: BLOCKED 项恢复后自动更新状态

### 4.5 速率限制与重试配置

- [ ] **知几 API** — 1秒限频，重试3次，间隔2秒
- [ ] **SMM** — 1.5秒限频，重试3次，Cloudflare bypass 集成
- [ ] **SHFE** — 2秒限频，重试2次，间隔5秒
- [ ] **Wind** — 按合同限制配置 (待签约)
- [ ] **ICSG** — 超时30s，重试2次，备用源降级
- [ ] **全局** — 爬虫并发限制 (默认1，可配置)
- [ ] **全局** — 爬虫失败冷却时间 (默认60秒)

### 4.6 备用数据源配置

- [ ] SPOT_IS: 100ppi.com → 备用: 生意社API
- [ ] CU_BALANCE_SHEET: ICSG → 备用: SMM (Cloudflare bypass)
- [ ] 库存数据: SHFE → 备用: Wind
- [ ] Top20持仓: Wind → 备用: SHFE公开数据
- [ ] 加工费: SMM → 备用: 行业协会
- [ ] 产量数据: 工业协会 → 备用: Wind
- [ ] 进口数据: 海关 → 备用: Wind
- [ ] 备用源切换逻辑已实现 (自动降级，手动确认)

---

## 5. Phase04 数据开发任务 (Phase04 Data Development Tasks)

### 5.1 36项新指标开发

#### 第1批: 数据源补充 (8.0人天) — Week 1-2

- [ ] **sn_spot_premium** — 锡现货升贴水 (知几API补充, 0.5人天)
- [ ] **ag_social_inventory** — 银社会库存 (知几API补充, 0.5人天)
- [ ] **sn_exchange_inventory** — 锡交易所库存 (SHFE补充, 0.5人天)
- [ ] **cu_smelter_production** — 铜冶炼产量 (工业协会, 1.5人天)
- [ ] **al_smelter_production** — 铝冶炼产量 (工业协会, 1.5人天)
- [ ] **cu_import_volume** — 铜进口量 (海关总署, 1.5人天)
- [ ] **al_import_volume** — 铝进口量 (海关总署, 1.5人天)
- [ ] **pb_acid_battery_output** — 铅酸电池产量 (统计局, 1.0人天)

#### 第2批: 新建爬虫 (14.0人天) — Week 3-5

- [ ] **cu_smelter_operating_rate** — 铜冶炼开工率 (代理估算+交叉验证, 2.0人天)
- [ ] **al_smelter_operating_rate** — 铝冶炼开工率 (代理估算+交叉验证, 2.0人天)
- [ ] **cu_tc** — 铜精矿加工费 (SMM, 1.0人天)
- [ ] **al_treatment_fee** — 铝加工费 (SMM, 1.0人天)
- [ ] **cu_smelter_profit** — 铜冶炼利润 (代理计算: 价格+加工费, 1.5人天)
- [ ] **al_smelter_profit** — 铝冶炼利润 (代理计算: 价格+加工费, 1.5人天)
- [ ] **cu_production_cost** — 铜生产成本 (代理估算+优化, 1.5人天)
- [ ] **al_production_cost** — 铝生产成本 (代理估算+优化, 1.5人天)

#### 第3批: 代理模型优化 (9.0人天) — Week 6-8

- [ ] **cu_terminal_demand** — 铜终端需求 (加入库存+消费季节性因子, 1.5人天)
- [ ] **al_terminal_demand** — 铝终端需求 (加入库存+消费季节性因子, 1.5人天)
- [ ] **cu_production_cost** — 铜生产成本 (加入能源价格因子, 1.5人天)
- [ ] **al_production_cost** — 铝生产成本 (加入能源价格因子, 1.5人天)
- [ ] **li_term_structure** — 锂期限结构 (优化代理模型, 1.5人天)
- [ ] **sn_top20_net** — 锡Top20净多 (补充历史Top20数据, 1.0人天)
- [ ] **cu_smelter_production** — 铜冶炼产量 (补充月度产量, 0.5人天)
- [ ] **al_smelter_production** — 铝冶炼产量 (补充月度产量, 0.5人天)

### 5.2 数据管道集成

- [ ] 36项指标爬虫统一调度器集成 (`schedule_crawler.py`)
- [ ] 数据管道流水线: 采集 → 清洗 → 转换 → 加载 → DQA验证
- [ ] 数据回填: 11项指标历史数据回填 (5.0人天 + 2.0人天清洗 + 1.5人天验证)
- [ ] 数据格式统一: JSONL 输出 → phase04_test.db 导入
- [ ] 增量更新策略: 每日定时爬取 + 增量导入
- [ ] 全量重建能力: 一键重建 phase04_test.db

### 5.3 DQA规则生产部署

- [ ] DQA-09~15 规则代码实装 (`scripts/dqa/rules/`)
- [ ] 36项指标 DQA 全量管道验证
- [ ] DQA-09 数据源交叉验证 (12项多源指标)
- [ ] DQA-10 代理估算置信度 (8项代理指标, 置信区间 < 95% 告警)
- [ ] DQA-11 月度/日度频率一致性 (6项跨频率指标)
- [ ] DQA-12 源时滞检测 (36项指标)
- [ ] DQA-13 历史覆盖率 (36项指标基线)
- [ ] DQA-14 依赖链一致性 (依赖DAG验证)
- [ ] DQA-15 日历豁免 (交易日历库)
- [ ] DQA CI/CD 集成: 每次提交自动运行全量DQA检查

### 5.4 监控与告警配置

- [ ] 噪声率实时监控 (1h采集间隔)
- [ ] 爬虫成功率监控 (按数据源/指标)
- [ ] DQA 通过率监控 (按规则/指标)
- [ ] CPU 基线监控 (2.0% 熔断阈值)
- [ ] 告警通道: ALERT-04 (Crawl Failed) / ALERT-05 (DQA Fail)
- [ ] 告警升级策略: WARN → HIGH → CRITICAL
- [ ] 告警自动恢复检测 (BLOCKED→恢复)
- [ ] 监控仪表盘: 噪声率/CPU/爬虫/DQA 四合一面板

### 5.5 性能基准测试

- [ ] 爬虫性能基准: 36项指标全量爬取耗时
- [ ] DQA 性能基准: 36项指标 × 15条规则全量验证耗时
- [ ] 数据库性能基准: phase04_test.db 查询性能
- [ ] 数据导入性能基准: JSONL → DB 导入耗时
- [ ] 降级性能基准: 8 BLOCKED 项降级切换耗时
- [ ] 内存占用基准: 爬虫+DQA+管道全链路内存峰值
- [ ] CPU 基准: 全链路 CPU 峰值 (目标 < 2.0%)

### 5.6 数据回填

| 指标 | 现有覆盖 | 目标覆盖 | 缺口 | 回填策略 | 工时 |
|------|:--------:|:--------:|:----:|----------|:----:|
| sn_spot_premium | 2018-至今 | 2015-至今 | 3年 | Wind补充 | 0.5d |
| ag_social_inventory | 2018-至今 | 2015-至今 | 3年 | Wind补充 | 0.5d |
| sn_exchange_inventory | 2015-至今 | 2010-至今 | 5年 | SHFE历史 | 0.5d |
| cu_smelter_production | 无 | 2018-至今 | 8年 | 协会API | 1.5d |
| al_smelter_production | 无 | 2018-至今 | 8年 | 协会API | 1.5d |
| cu_import_volume | 无 | 2015-至今 | 11年 | 海关API | 1.5d |
| al_import_volume | 无 | 2015-至今 | 11年 | 海关API | 1.5d |
| pb_acid_battery_output | 无 | 2015-至今 | 11年 | 统计局 | 1.0d |
| cu_tc | 无 | 2015-至今 | 11年 | SMM | 0.5d |
| al_treatment_fee | 无 | 2015-至今 | 11年 | SMM | 0.5d |
| sn_top20_net | 无 | 2015-至今 | 11年 | Wind | 0.5d |

- [ ] 11项指标历史数据回填完成
- [ ] 数据清洗 + 去重 (2.0人天)
- [ ] 交叉验证 (1.5人天)
- [ ] 回填数据通过 DQA 全部15条规则验证

---

## 6. Phase04→Phase05 交接标准 (Phase04→Phase05 Handover Criteria)

### 6.1 必达标准 (Mandatory Gates)

- [ ] **36项指标全部通过 DQA** — 15条规则全部PASS (DQA-01~15)
- [ ] **噪声率 < 10% 持续达标** — 7天静默期噪声率观测完成
- [ ] **CPU 基线在阈值内** — 全链路 CPU 峰值 < 2.0%
- [ ] **爬虫运行时间 > 99%** — 36项指标爬虫月度可用率 > 99%
- [ ] **所有 BLOCKED 项已解决或降级+CI** — 8项 BLOCKED 降级逻辑已集成且有 CI 验证
- [ ] **P0-13 门禁关闭** — 168h 噪声观测完成，噪声率 < 10%
- [ ] **P0-12 门禁关闭** — CPU 基线达标或 HERMES 豁免已批准
- [ ] **Wind 授权已签署** — 2026-11-07 目标签约完成

### 6.2 数据质量标准

| 维度 | 目标值 | 验证方式 |
|------|:------:|----------|
| 数据完整性 | 36/36 指标有数据 | DQA-01 (空值检测) |
| 数据一致性 | 多源交叉偏差 < 5% | DQA-09 (交叉验证) |
| 数据时效性 | 日度指标 < 24h延迟 | DQA-12 (源时滞) |
| 历史覆盖率 | ≥ 95% (目标年份) | DQA-13 (历史覆盖) |
| 依赖链一致性 | 0 断裂 | DQA-14 (依赖链) |
| 日历豁免正确 | 100% | DQA-15 (日历豁免) |

### 6.3 性能标准

| 维度 | 目标值 |
|------|:------:|
| 全量爬取耗时 | < 2小时 (36指标) |
| DQA 全量验证耗时 | < 30分钟 (36指标 × 15规则) |
| 数据库查询性能 | 单指标查询 < 500ms |
| 数据导入性能 | 100万行 < 10分钟 |
| 降级切换耗时 | < 5秒 |
| CPU 峰值 | < 2.0% |
| 内存峰值 | < 512MB |

### 6.4 文档标准

- [ ] Phase04 数据侧综合报告
- [ ] 36项指标数据源注册表
- [ ] DQA-09~15 规则实装文档
- [ ] 爬虫架构文档
- [ ] 数据管道架构文档
- [ ] 性能基准测试报告
- [ ] 风险台账更新 (所有 Phase04 新增风险)
- [ ] 运维手册 (含故障排查指南)

### 6.5 HERMES 审批

- [ ] Phase04 启动审批 (HERMES)
- [ ] P0-13 噪声基线确认 (HERMEShf)
- [ ] P0-12 CPU 基线确认 (HERMES)
- [ ] Wind 授权签约确认
- [ ] Phase04→Phase05 交接审批

---

## 7. 环境变量与配置 (Environment Variables and Configuration)

### 7.1 必需环境变量

| 变量名 | 用途 | 值/示例 | 必需 |
|--------|------|---------|:----:|
| `V88_PHASE03_TEST_DB` | Phase03 测试库路径 | `analysis/e2e_output/v88/phase03/p0/phase03_test.db` | ✅ |
| `V88_PHASE04_TEST_DB` | Phase04 测试库路径 | `analysis/e2e_output/v88/phase04/phase04_test.db` | ✅ |
| `V88_API_CACHE_DB` | API缓存库路径 | `scripts/api_cache.db` | ✅ |
| `V88_CRAWLER_CONFIG` | 爬虫配置文件路径 | `scripts/crawler/crawler_config.yaml` | ✅ |
| `V88_DQA_CONFIG` | DQA配置文件路径 | `scripts/dqa/dqa_config.yaml` | ✅ |
| `V88_THRESHOLD_CONFIG` | 阈值配置路径 | `scripts/threshold_config.yaml` | ✅ |
| `V88_DEGRADE_CONFIG` | 降级配置路径 | `scripts/degrade_config.yaml` | ✅ |
| `V88_INDICATOR_REGISTRY` | 指标注册表路径 | `data/indicator_registry.json` | ✅ |
| `V88_DATA_SOURCE_MAPPING` | 数据源映射表路径 | `data/data_source_mapping.json` | ✅ |
| `V88_DEPENDENCY_DAG` | 依赖DAG路径 | `data/indicator_dependency_dag.json` | ✅ |
| `V88_TRADING_CALENDAR` | 交易日历路径 | `data/trading_calendar.json` | ✅ |
| `V88_ZHIJI_API_KEY` | 知几API密钥 | (存储于 ~/.hermes/) | ✅ |
| `V88_WIND_API_TOKEN` | Wind API Token | (签约后生成) | ⏳ |
| `V88_SMM_API_KEY` | SMM API密钥 | (待配置) | ⏳ |
| `V88_DB_QUERY_TIMEOUT_MS` | 数据库查询超时 | `5000` | ⚠️ |
| `V88_CRAWLER_CONCURRENCY` | 爬虫并发数 | `1` | ⚠️ |
| `V88_CRAWLER_RETRY_MAX` | 爬虫最大重试次数 | `3` | ⚠️ |
| `V88_CRAWLER_RETRY_DELAY` | 爬虫重试间隔(秒) | `2` | ⚠️ |
| `V88_NOISE_OBSERVATION` | 噪声观测使能 | `true` | ⚠️ |
| `V88_DQA_STRICT_MODE` | DQA严格模式 | `true` | ⚠️ |

### 7.2 配置文件路径与Schema

#### crawler_config.yaml
```yaml
sources:
  zhiji:
    enabled: true
    rate_limit: 1.0
    retry:
      max_attempts: 3
      delay: 2.0
  smm:
    enabled: true
    rate_limit: 1.5
    cloudflare_bypass: true
    retry:
      max_attempts: 3
      delay: 1.5
  shfe:
    enabled: true
    rate_limit: 2.0
    retry:
      max_attempts: 2
      delay: 5.0
  wind:
    enabled: false  # 签约后启用
    rate_limit: 1.0
global:
  concurrency: 1
  cool_down_seconds: 60
  timeout_ms: 30000
```

#### dqa_config.yaml
```yaml
rules:
  DQA-01: { enabled: true, severity: CRITICAL }
  DQA-02: { enabled: true, severity: CRITICAL }
  DQA-03: { enabled: true, severity: WARN, threshold: 90 }
  DQA-04: { enabled: true, severity: CRITICAL, sigma: 3 }
  DQA-05: { enabled: true, severity: WARN }
  DQA-06: { enabled: true, severity: CRITICAL, max_drift_days: 365 }
  DQA-07: { enabled: true, severity: WARN }
  DQA-08: { enabled: true, severity: WARN }
  DQA-09: { enabled: true, severity: CRITICAL, max_deviation_pct: 5 }
  DQA-10: { enabled: true, severity: WARN, min_confidence_pct: 95 }
  DQA-11: { enabled: true, severity: WARN }
  DQA-12: { enabled: true, severity: WARN, max_lag_hours: 48 }
  DQA-13: { enabled: true, severity: WARN, min_coverage_pct: 95 }
  DQA-14: { enabled: true, severity: CRITICAL }
  DQA-15: { enabled: true, severity: WARN }
strict_mode: true
```

#### threshold_config.yaml
```yaml
levels:
  normal:
    low_percentile: 10
    high_percentile: 90
  warning:
    low_percentile: 5
    high_percentile: 95
  circuit_breaker:
    low_percentile: 0
    high_percentile: 100
cpu:
  peak_pct: 2.0
noise:
  max_rate_pct: 10.0
  safety_margin_pct: 2.0
```

#### degrade_config.yaml
```yaml
blocked_items:
  - id: BLOCKED-01
    indicator: cu_smelter_production
    degrade_strategy: proxy_estimation_with_monthly_interpolation
    trigger_condition: crawler_fail
    recovery_condition: data_source_restored
  - id: BLOCKED-02
    indicator: al_smelter_production
    degrade_strategy: proxy_estimation_with_monthly_interpolation
    trigger_condition: crawler_fail
    recovery_condition: data_source_restored
  # ... BLOCKED-03 ~ BLOCKED-08
```

### 7.3 服务账号与权限

| 账号 | 用途 | 权限 | 状态 |
|------|------|:----:|:----:|
| `dshb_agent` | DSHB数据侧agent | analysis/写权限 | ✅ |
| `dshb_crawler` | 爬虫服务账号 | 数据源API访问 | ⏳ |
| `dshb_dqa` | DQA校验服务账号 | 数据库读权限 | ✅ |
| `dshb_backup` | 备份服务账号 | 数据库读写 | ✅ |
| `wind_service` | Wind API服务 | Wind数据访问 | ⏳ |
| `dshb_monitor` | 监控服务账号 | 日志读取+告警发送 | ⏳ |

### 7.4 密钥管理策略

- [ ] 知几 API key: 存储在 `~/.hermes/scripts/zhiji_api.py`，不进 Git 仓库
- [ ] Wind API Token: 签约后存储于 `~/.hermes/config/wind_token.env`
- [ ] SMM API key: 存储于 `~/.hermes/config/smm_key.env`
- [ ] 所有密钥文件权限: 600 (仅所有者可读写)
- [ ] 密钥轮换策略: 每90天轮换一次
- [ ] 密钥审计: 每月检查密钥使用情况

---

## 8. 时间线与里程碑 (Timeline and Milestones)

### 8.1 13周总体计划

| 周次 | 日期范围 (预估) | 阶段 | 关键任务 | 交付物 | 里程碑 |
|:----:|:--------------:|------|----------|--------|:------:|
| **W1** | 10/24 ~ 10/30 | 环境设置 | 环境配置/目录创建/API密钥管理/配置模板 | 环境配置完成报告 | — |
| **W2** | 10/31 ~ 11/06 | 数据管道 | 数据管道搭建/爬虫调度器/数据源注册表 | 数据管道架构文档 | **M1: 环境就绪** |
| **W3** | 11/07 ~ 11/13 | 爬虫开发 | 第1批数据源补充(8项)/爬虫调度器 | 8项指标DQA PASS | **M2: Wind签约** |
| **W4** | 11/14 ~ 11/20 | 爬虫开发 | 第2批新建爬虫(4项)/Cloudflare bypass | 4项爬虫DQA PASS | — |
| **W5** | 11/21 ~ 11/27 | 爬虫开发 | 第2批新建爬虫(4项)/爬虫测试 | 8项新建爬虫完成 | **M3: 爬虫上线** |
| **W6** | 11/28 ~ 12/04 | DQA部署 | DQA-09~15规则实装 | 7条规则实装 | — |
| **W7** | 12/05 ~ 12/11 | DQA部署 | DQA单元测试/集成测试 | 测试报告 | — |
| **W8** | 12/12 ~ 12/18 | DQA部署 | DQA CI/CD集成/第3批代理优化 | 第3批指标完成 | **M4: DQA就绪** |
| **W9** | 12/19 ~ 12/25 | 集成测试 | 全量集成测试/性能基准 | 集成测试报告 | — |
| **W10** | 12/26 ~ 01/01 | 集成测试 | 性能调优/数据回填 | 回填完成报告 | — |
| **W11** | 01/02 ~ 01/08 | 集成测试 | 监控告警配置/降级逻辑验证 | 监控仪表盘 | **M5: 性能达标** |
| **W12** | 01/09 ~ 01/15 | 最终验证 | 全量验证/文档编制 | 验证报告 | — |
| **W13** | 01/16 ~ 01/22 | 最终验证 | 交接准备/HERMES审批 | 交接文档 | **M6: 交接完成** |

### 8.2 关键路径

```
Phase03收尾 (P0-13观测) ──→ 环境设置(W1) ──→ 数据管道(W2)
                                           ↓
                           Wind签约(W3) ──→ 爬虫开发(W3-W5)
                                              ↓
                               DQA规则实装(W6-W8) ──→ 集成测试(W9-W11)
                                                                    ↓
                                                              最终验证(W12-W13) ──→ Phase05
```

### 8.3 关键依赖

| 依赖项 | 影响周次 | 截止日 | 负责方 |
|--------|:--------:|:------:|:------:|
| P0-13 168h 观测完成 | W1 | 2026-10-22 | DSHB |
| Wind 授权签约 | W3 | 2026-11-07 | 财务+DSHB |
| Wind API Token | W3 | 2026-11-03 | DSHB |
| SMM 数据授权 | W4 | 2026-11-14 | DSHB |
| 海关总署数据授权 | W3 | 2026-11-10 | DSHB |
| DSHE 集成团队排期 | W2 | 2026-10-28 | DSHB+DSHE |
| DQA-09~15 规则设计定稿 | W6 | 2026-11-28 | DSHB |

### 8.4 风险窗口

| 时间窗口 | 风险 | 缓解措施 |
|----------|------|----------|
| W1-W2 | P0-13 未按时完成 | 噪声率 7.54% 已达标，安全裕度 2.46pp |
| W3 | Wind 签约延迟 | 并行启动备选数据源 (SHFE公开数据) |
| W4-W5 | 爬虫反爬问题 | 复用 Phase03 Cloudflare bypass 方案 |
| W6-W8 | DQA规则开发延迟 | 分批交付，优先级排序 |
| W9-W11 | 数据质量异常 | DQA-09/10 自动检测+告警 |
| W12-W13 | 交接审批延迟 | 提前准备交接文档，预留缓冲 |

---

## 9. 风险追踪 (Risk Items to Track)

### 9.1 Phase03 遗留风险

| 编号 | 风险 | 等级 | 状态 | 负责方 | 预期闭环 |
|------|------|:----:|:----:|:------:|:--------:|
| **R-V88-034** | CPU基线优化(P0-12门禁) | P2 | 🟡 MITIGATED (EXEMPTION_GRANTED) | DSHB | 已豁免 |
| **R-V88-035** | 告警噪声率7天观测(P0-13门禁) | P2 | 🟡 IN_PROGRESS (148/168h, 88.1%) | DSHB+HERMES | 2026-10-22 |
| **R-V88-036** | 180指标扩量可追溯(P0-14门禁) | P2 | 🟢 MITIGATED | DSHB | 已完成 |
| **R-V88-037** | 派生指标零值数据源缺失 | P2 | ✅ CLOSED (8/9修复, 1项PARTIAL) | DSHB | 已完成 |
| **R-V88-038** | 派生指标连续相同值(数据停滞) | P2 | 🟡 MONITORED | DSHB | 持续观察 |

### 9.2 Phase04 新增风险

| 编号 | 风险 | 等级 | 状态 | 负责方 | 缓解措施 |
|------|------|:----:|:----:|:------:|----------|
| **R-V88-043** | SPOT_IS爬虫URL变更导致数据采集失败 | P1 | 🟡 TRACKING | DSHB | SPOT_IS v2 已修复5项URL；持续监控HTTP错误率 |
| **R-V88-044** | SMM Cloudflare反爬策略升级导致bypass失效 | P1 | 🟡 TRACKING | DSHB | 4层重试策略+备用源降级；定期更新bypass策略 |
| **R-V88-046** | 新增DQA-09~15规则开发延迟影响Phase04进度 | P2 | 🟡 TRACKING | DSHB | 分批交付(DQA-09~12优先)；设计草案已就绪 |
| **R-V88-048** | 36项指标数据源授权延迟(海关/工业协会/统计局) | P1 | 🟡 TRACKING | DSHB | 并行启动多个数据源申请；备选数据源策略 |
| **R-V88-049** | Phase04计划延期 (12周→13周) | P2 | 🟡 TRACKING | DSHB+HERMES | 59.5人天/13周已预留缓冲；分批交付降低风险 |
| **R-V88-042** | Wind授权签约延迟 (ni_top20_net数据源) | P1 | 🔴 PENDING | DSHB+财务 | 目标2026-11-07签约；备选: SHFE公开Top20数据 |
| **R-V88-050** | 代理估算模型精度不足 (8项代理指标) | P2 | 🟡 TRACKING | DSHB | DQA-10置信度检测；双源交叉验证；人工校准 |
| **R-V88-051** | 数据回填历史数据质量不一致 | P2 | 🟡 TRACKING | DSHB | 回填后DQA全量验证；交叉验证；数据清洗 |
| **R-V88-052** | 爬虫并发导致API限频/封禁 | P2 | 🟡 TRACKING | DSHB | 速率限制配置；冷却时间策略；备用代理池 |
| **R-V88-053** | 8项BLOCKED降级逻辑集成复杂度超预期 | P2 | 🟡 TRACKING | DSHB | 降级逻辑已设计；分阶段实装；自动化测试覆盖 |

### 9.3 风险热力图

| 风险 | 概率 | 影响 | 风险等级 | 优先级 |
|------|:----:|:----:|:--------:|:------:|
| R-V88-042 Wind签约延迟 | 中 | 高 | 🔴 HIGH | P0 |
| R-V88-043 SPOT_IS URL变更 | 中 | 中 | 🟡 MEDIUM | P1 |
| R-V88-044 SMM Cloudflare升级 | 中 | 高 | 🔴 HIGH | P1 |
| R-V88-046 DQA规则延迟 | 低 | 高 | 🟡 MEDIUM | P2 |
| R-V88-048 数据源授权延迟 | 高 | 高 | 🔴 HIGH | P0 |
| R-V88-049 计划延期 | 中 | 中 | 🟡 MEDIUM | P2 |
| R-V88-050 代理模型精度 | 中 | 中 | 🟡 MEDIUM | P2 |
| R-V88-051 回填数据质量 | 中 | 中 | 🟡 MEDIUM | P2 |
| R-V88-052 API限频/封禁 | 低 | 中 | 🟡 MEDIUM | P3 |
| R-V88-053 降级逻辑复杂度 | 低 | 中 | 🟡 MEDIUM | P3 |

### 9.4 风险监控计划

- [ ] **每周风险评审** — 每周一 10:00 更新风险台账状态
- [ ] **每日告警检查** — 检查爬虫/DQA告警日志
- [ ] **噪声率日监控** — 每小时采集，每日汇总
- [ ] **P0-13观测监控** — 88.1% → 100% (最后20h)
- [ ] **Wind签约进度追踪** — C01~C12 检查项每周更新
- [ ] **数据源授权追踪** — 海关/工业协会/统计局 授权进度周报

---

## 10. 签核要求 (Sign-off Requirements)

### 10.1 数据完整性签核

| 检查项 | 标准 | 签核人 | 签核日期 | 状态 |
|--------|:----:|:------:|:--------:|:----:|
| phase03_test.db 完整性 | 718指标/590,455行/0冲突 | DSHB | 待签核 | ⏳ |
| 36项指标数据注册 | 36/36 已注册 | DSHB | 待签核 | ⏳ |
| 数据日期范围 | 覆盖目标年份 ≥ 95% | DSHB | 待签核 | ⏳ |
| 数据源映射 | 36/36 已映射 | DSHB | 待签核 | ⏳ |
| 派生指标 | 70/70 已入库 | DSHB | 待签核 | ⏳ |
| **数据完整性总签核** | **全部PASS** | **DSHB** | **待签核** | **⏳** |

### 10.2 DQA 通过率签核

| 检查项 | 标准 | 签核人 | 签核日期 | 状态 |
|--------|:----:|:------:|:--------:|:----:|
| DQA-01~08 基线 | 8/8 PASS | DSHB | 待签核 | ⏳ |
| DQA-09 交叉验证 | 12项多源指标 PASS | DSHB | 待签核 | ⏳ |
| DQA-10 代理置信度 | 8项代理指标 PASS | DSHB | 待签核 | ⏳ |
| DQA-11 频率一致性 | 6项跨频率指标 PASS | DSHB | 待签核 | ⏳ |
| DQA-12 源时滞 | 36项指标 PASS | DSHB | 待签核 | ⏳ |
| DQA-13 历史覆盖 | ≥ 95% | DSHB | 待签核 | ⏳ |
| DQA-14 依赖链 | 0断裂 | DSHB | 待签核 | ⏳ |
| DQA-15 日历豁免 | 100% | DSHB | 待签核 | ⏳ |
| **DQA总签核** | **15/15 PASS** | **DSHB** | **待签核** | **⏳** |

### 10.3 性能基准签核

| 检查项 | 目标值 | 实测值 | 签核人 | 签核日期 | 状态 |
|--------|:------:|:------:|:------:|:--------:|:----:|
| 全量爬取耗时 | < 2小时 | 待测 | DSHB | 待签核 | ⏳ |
| DQA全量验证耗时 | < 30分钟 | 待测 | DSHB | 待签核 | ⏳ |
| 数据库查询性能 | < 500ms/查询 | 待测 | DSHB | 待签核 | ⏳ |
| 数据导入性能 | 100万行 < 10分钟 | 待测 | DSHB | 待签核 | ⏳ |
| CPU峰值 | < 2.0% | 待测 | DSHB | 待签核 | ⏳ |
| 内存峰值 | < 512MB | 待测 | DSHB | 待签核 | ⏳ |
| 降级切换耗时 | < 5秒 | 待测 | DSHB | 待签核 | ⏳ |
| **性能总签核** | **全部达标** | — | **DSHB** | **待签核** | **⏳** |

### 10.4 HERMES 审批

| 审批项 | 审批人 | 审批日期 | 状态 |
|--------|:------:|:--------:|:----:|
| Phase04 启动审批 | HERMES | 待审批 | ⏳ |
| P0-13 噪声基线确认 | HERMEShf | 待审批 | ⏳ |
| P0-12 CPU基线确认 | HERMES | 已批准 (EXEMPTION_GRANTED) | ✅ |
| Wind 授权签约确认 | HERMES | 待审批 | ⏳ |
| Phase04→Phase05 交接审批 | HERMES | 待审批 | ⏳ |

### 10.5 签核流程

```
DSHB 数据完整性签核 ──→ DSHB DQA通过率签核 ──→ DSHB 性能基准签核
                                                    ↓
                                            HERMES Phase04 启动审批
                                                    ↓
                                            HERMES P0-13 基线确认
                                                    ↓
                                            HERMES Phase04→Phase05 交接审批
```

### 10.6 签核门槛

Phase04→Phase05 交接必须满足以下全部条件：
- [ ] 3项 DSHB 内部签核完成 (数据完整性 + DQA通过率 + 性能基准)
- [ ] HERMES 4项审批完成 (启动 + P0-13 + P0-12 + 交接)
- [ ] 所有 P0/P1 风险项已 CLOSED 或 MITIGATED
- [ ] 所有交接文档已归档
- [ ] 运维手册已交付

---

## 11. 附录 (Appendix)

### A.1 Phase03 关键交付物索引

| # | 文件 | 用途 | 路径 |
|:-:|------|------|------|
| 1 | `v88_phase03_p1_dshb_main_report.md` | P1综合报告 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 2 | `v88_phase03_p1_dshb_risklist.md` | 风险台账 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 3 | `v88_phase03_p1_noise_rate_analysis.md` | 噪声率分析 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 4 | `v88_phase03_p1_3level_threshold_baseline.md` | 三级阈值基线 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 5 | `v88_phase03_p1_metric_indicator_code_mapping.md` | 指标映射表 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 6 | `v88_phase03_p1_base_indicator_expansion.md` | 基础指标扩量报告 | `analysis/e2e_output/v88/phase03/p1/dshb/` |
| 7 | `noise_7d_log.jsonl` | 噪声观测日志 | `analysis/e2e_output/v88/phase03/p1/dshb/followup/` |
| 8 | `phase04_dqa_rules_draft.md` | DQA规则设计草案 | `analysis/e2e_output/v88/phase03/p1/dshb/background_final_prep/` |
| 9 | `spotis_url_fix_report.md` | SPOT_IS URL修复报告 | `analysis/e2e_output/v88/phase03/p1/dshb/background_final_prep/` |
| 10 | `smm_cloudflare_bypass_package.md` | SMM bypass方案 | `analysis/e2e_output/v88/phase03/p1/dshb/background_final_prep/` |
| 11 | `wind_authorization_precheck.md` | Wind授权预检 | `analysis/e2e_output/v88/phase03/p1/dshb/background_final_prep/` |
| 12 | `v88_phase04_36metric_data_source_plan.md` | 36指标数据源规划 | `analysis/e2e_output/v88/phase03/p1/dshb/background_continue/` |

### A.2 关键指标速查

| 指标 | Phase03 值 | Phase04 目标 | 变化 |
|------|:----------:|:------------:|:----:|
| 总指标数 | 718 | 754 (+36) | +5.0% |
| DQA规则数 | 8 | 15 | +87.5% |
| 噪声率 | 7.54% | < 10% | — |
| CPU峰值 | 0.0654% | < 2.0% | — |
| 爬虫数 | ~5 | ~20 | +300% |
| BLOCKED项 | 8 | 0 (降级+CI) | -100% |
| 风险项 | 19 | ~30 (含新增) | +57.9% |
| 数据源数 | ~8 | ~15 | +87.5% |
| 品种覆盖 | 12 | 9 (新增36指标) | — |

### A.3 文件清单 (本文档)

| 文件 | 类型 | 大小 |
|------|------|-----:|
| `dshb_phase04_bootstrap_checklist.md` | 本文档 | — |

### A.4 后续文档计划

- [ ] `v88_phase04_data_pipeline_architecture.md` — 数据管道架构文档 (W2)
- [ ] `v88_phase04_dqa_rules_implementation.md` — DQA规则实装文档 (W8)
- [ ] `v88_phase04_crawler_architecture.md` — 爬虫架构文档 (W5)
- [ ] `v88_phase04_performance_benchmark.md` — 性能基准测试报告 (W11)
- [ ] `v88_phase04_operations_manual.md` — 运维手册 (W13)

---

## 12. 元数据标记

```
PHASE04_BOOTSTRAP_CHECKLIST=TRUE
PHASE04_BOOTSTRAP_CHECKLIST=READY_FOR_REVIEW
V88_PHASE03_P1_DSHB_PREP_P013_CLOSE_JOB=T4_COMPLETE
P0_13_NOISE_BASELINE=PENDING (148/168h, 88.1%)
P0_12_CPU_BASELINE=DONE (EXEMPTION_GRANTED)
PHASE04_PLAN=59.5_PERSON_DAYS_13_WEEKS
PHASE04_METRICS=36
PHASE04_DQA_RULES=15 (8 existing + 7 new)
PHASE04_RISK_ITEMS=14 (5 legacy + 9 new)
BRANCH_LOCKED=feature/v88-g1
```

---

*Document Generated: 2026-10-24*
*Generated by: DSHB Agent (T4)*
*Branch: feature/v88-g1 (BRANCH_LOCKED)*
*Schema: v88-phase04-bootstrap-v1.0*
*Status: PHASE04_BOOTSTRAP_CHECKLIST_READY_FOR_REVIEW*
