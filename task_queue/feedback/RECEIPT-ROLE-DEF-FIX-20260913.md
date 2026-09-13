# 任务回执：修正 DSHARNES_B_ROLE_DEF.md（爱马仕审计 4 项对齐）

> 回执编号: RECEIPT-ROLE-DEF-FIX-20260913
> 发送者: Dsharnes-B
> 接收者: 爱马仕（主脑）
> 生成时间: 2026-09-13
> 审计来源: commit `217cb86` · `audit_dsharnes_b_role_20260913.md`
> 分支: `indicator-correction-win`

---

## 任务概要

依据爱马仕 2026-09-13 单次手动审计（`work_log/hermes_daily_report/audit_dsharnes_b_role_20260913.md`，4 项 🟡 中等问题，无阻断项），对 `docs/DSHARNES_B_ROLE_DEF.md` 进行 v1.0 → v1.1 修订，全部 4 项已对齐。

---

## 4 项对齐明细

| 编号 | 审计发现 | 修正内容 | 落点 |
|---|---|---|---|
| **R1** | Dsharnes-A/B 术语与 AGENTS.md 线A/线B 语义相反 | 新增「§〇 术语备注」：明确两套命名体系不同维度（写权限隔离 vs 跨服务器算力分工），附冲突提示 + 判断规则 | 第 10-22 行 |
| **R2** | B 对 framework-tree 读写权过宽，未声明 chart_kits.py / indicators_v1.json 限制 | 新增「§5.2 文件级读写约束」：chart_kits.py 禁止修改（仅主脑可改）、indicators_v1.json 仅可读不可写、tree_config.json / 三道门禁脚本同样禁止；同步写入 §一 禁止项表 + §六 常驻规则第 10 条 | 第 48-50、218-240、255 行 |
| **G1** | `[B]` 前缀与项目「数据类」冲突 | §3.1 提交前缀改为 `[WEB]`（看板/页面/前端代码）+ `[DOC]`（文档/回执），明确 `[B]` 禁止使用（项目 `[B]`=数据类），附正确示例 + 旧格式拒绝示例；§六 常驻规则第 8 条 | 第 90-119、253 行 |
| **G2** | 未提及 pre-commit hook 强制机制 | 新增「§3.2 pre-commit hook 强制机制」：hook 规则说明 + B 标准应对流程（改 HTML 须同步 STATUS.md）+ `--no-verify` 逃生通道限定表（仅看板/文档可用，核心业务代码禁止）+ 拦截处理流程；§一 禁止项 + §六 常驻规则第 9 条 | 第 121-154、50、254 行 |

---

## 产出文件清单

| 文件 | 状态 | 行数 |
|---|---|---|
| `docs/DSHARNES_B_ROLE_DEF.md` | ✏️ 修改（v1.0 154 行 → v1.1 260 行） | +106 行 |
| `task_queue/feedback/RECEIPT-ROLE-DEF-FIX-20260913.md` | ✅ 新建（本回执） | — |

---

## 约束遵守确认

| 约束 | 状态 |
|---|---|
| 仅提交 `indicator-correction-win`，严禁提交 main | ✅ |
| 禁止运行大规模回测 | ✅ 未运行任何回测 |
| 需数据运算时生成工单交 Dsharnes-A | ✅ 本任务无需运算，未生成工单 |
| 不修改业务源码 | ✅ 仅修改 `docs/DSHARNES_B_ROLE_DEF.md` |
| 不改动 `unified_venv` | ✅ |
| 不修改 `chart_kits.py` / `indicators_v1.json` | ✅ |
| 不使用 `[B]` 前缀 | ✅ 使用 `[WEB]` / `[DOC]` |

---

## 验收确认

- [x] R1 术语备注已补充（两套命名体系区分 + 冲突提示 + 判断规则）
- [x] R2 文件读写约束已补充（chart_kits.py 禁止 / indicators_v1.json 仅可读 / 仅主脑可改）
- [x] G1 提交前缀已修正（[B] → [WEB]，区分数据类标签）
- [x] G2 pre-commit hook 说明已补充（hook 规则 + 应对流程 + --no-verify 逃生通道 + 核心代码禁止）
- [x] 版本升级 v1.0 → v1.1，变更日志写入文件头
- [x] 常驻规则从 7 条扩展至 11 条，覆盖全部新增约束
- [x] 工单路径修正为 `task_queue/to_A/`（与实际目录一致）

**状态: ✅ 完成，等待爱马仕 v4 轮询自动审计**
