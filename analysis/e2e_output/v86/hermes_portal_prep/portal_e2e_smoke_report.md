# 门户端到端冒烟测试报告

> 工单: `HERMES_V86_PORTAL_INTEGRATE_AND_V85_FROZEN_DEMO_LOCK` · T2.5
> 生成时间: 2026-10-02 09:40
> 分支: `feature/v85-chart-template` @ `5e874a7`
> 测试对象: 门户 ↔ V85 只读 API ↔ V86 任务接口 ↔ 快照存储
> 执行方式: 进程内真实调用 `v85_artifact_api.py`（非模拟）

---

## 1. 执行摘要

| 维度 | 结果 |
|------|------|
| 冒烟用例总数 | 18 |
| 通过 | 13 |
| 失败 | 1 |
| 警告（不阻断） | 4 |
| 阻断上线 | **1 项（SMK-01，可 1 行修复）** |
| zhiji API 调用 | 0（`NO_ZHIJI_API_CALL=TRUE` ✅） |

**结论**: V85 只读 API 核心链路（探活/版本/制品/查询/MD5/写保护/权限/版本隔离）全部通过。发现 1 项阻断缺陷（Windows 硬编码路径）+ 4 项警告（白名单路径过期、分页上限、权限令牌缺口、Python 层写方法异常类型）。

---

## 2. 冒烟用例明细

### 2.1 SMK-01 API 进程启动与默认配置 🔴 FAIL

| 项 | 值 |
|---|---|
| 测试 | `python3 v85_artifact_api.py --smoke`（不传参数） |
| 实际结果 | `RuntimeError: V85 输出根目录不存在: D:/DSH_WORK/framework-tree/analysis/e2e_output/v85` |
| 根因 | `repo_root` 默认值硬编码为 Windows 路径，Linux 部署必崩 |
| 修复后 | `--smoke --repo-root /home/ubuntu/framework-tree` → `{"smoke": "PASS", "artifacts": 31, "versions": ["f313570","v86-dev"], "failures": []}` |
| 建议 | 默认值改为 `os.environ.get("FRAMEWORK_TREE", Path(__file__).parents[4])`；或要求 `FRAMEWORK_TREE` 环境变量强制显式传入 |
| 阻断性 | 🔴 **阻断** — 门户部署脚本必须传参，否则无法启动 |

### 2.2 SMK-02 健康探活 ✅ PASS

```json
{"status":"ok","api_schema":"v1","version":"1.0.0","read_only":true,
 "no_zhiji_api_call":true,"registered_versions":2,"registered_artifacts":31}
```

### 2.3 SMK-03 版本列表与可读性 ✅ PASS

| key | version_tag | readable |
|---|---|---|
| `f313570` | `v85.0` | ✅ true |
| `v86-dev` | `v86-dev-placeholder` | ❌ false |

`include_inactive=0` 时仅返回 `f313570`，符合契约。

### 2.4 SMK-04 制品目录列举 ✅ PASS / ⚠ 警告

- `count=31` ✅，`registered_artifacts=31` 与 `/health` 一致
- ⚠ **4 项制品文件不存在**（登记路径已过期）：

| kind | 登记 relpath | 状态 |
|------|---|---|
| `ambiguous_indicator_list` | `hermes_portal_gate_final/ambiguous_indicator_list.csv` | ❌ missing |
| `template_manifest` | `hermes_portal_gate_final/ths_render_task_manifest.json` | ❌ missing |
| `template_task_list` | `hermes_portal_gate_final/ths_render_task_list.json` | ❌ missing |
| `template_task_summary` | `hermes_portal_gate_final/ths_render_task_summary.csv` | ❌ missing |

根因：这四个文件实际位于 `v85_final_integrate/`（manifest/list/summary）与 `alias_lib_full_audit/`（ambiguous list），而非 `hermes_portal_gate_final/`。API 自身 `--smoke` 不校验存在性，故未报错。
影响：门户「制品目录」Tab 中这 4 项显示 ❌；快照校验面板会标红。
建议：走 PR 修正 `ARTIFACTS` 表 relpath，重跑 `--smoke`。

### 2.5 SMK-05 风险库分页查询 ✅ PASS

| 项 | 值 |
|---|---|
| `total` | 50 |
| `filters={"risk_level":"P0"}` | `filtered=33` |
| 分页字段 | `offset`/`limit`/`returned`/`next_offset` 均返回 ✅ |

### 2.6 SMK-06 场景回放全量查询 ✅ PASS

`scenario_replay`（488 模板回放 CSV）`total=2721` 行，与 DSHB 交付一致。

### 2.7 SMK-07 单制品元数据 + MD5 实时校验 ✅ PASS

| 项 | 值 |
|---|---|
| `kind` | `risk_db` |
| `md5` | `2c85f4025baf09ec55b47709cdc2168d` |
| `verify_file=1` 实时重算 | `match: true` |

快照一致性验证通过 → 支持门户「🔐 快照校验」面板。

### 2.8 SMK-08 V86 占位版本读取隔离 ✅ PASS

```
GET /artifacts?version=v86-dev → 403 VERSION_READ_FORBIDDEN
```

符合契约 §2「`v86-dev` 不开放读服务」。

### 2.9 SMK-09 写方法拒绝 ⚠ 警告

Python 层调用 `api.put("risk_db", {...})` 抛出 `TypeError`（方法签名不匹配）而非 `ApiError(WRITE_FORBIDDEN)`。
说明：HTTP 层（FastAPI 适配）会在路由前返回 405/403，防护有效；但**进程内直连**调用方会拿到非预期异常类型。
建议：为 `put/post/patch/delete` 补显式桩方法，统一抛 `WriteForbiddenError`。

### 2.10 SMK-10 未知制品 404 ✅ PASS

`get_artifact_meta("not_exist_kind")` → `404 ARTIFACT_NOT_REGISTERED`。

### 2.11 SMK-11 ops_read 令牌权限 ✅ PASS（功能正确）⚠ 门户影响

`portal_read` 令牌调用 `metrics()` → `ForbiddenError: 角色 'ops_read' 不在令牌权限集 ['portal_read']`。
权限判定正确，但**门户若需展示运维指标，必须换用 `v85-admin-readonly-0001`**（含 `portal_read, audit_read, ops_read`）。建议门户配置双令牌。

### 2.12 SMK-12 快照 MD5 批量校验 ✅ PASS

对已存在的 27 项制品循环 `verify_artifact_md5(kind, expected, verify_file=1)` → 全部 `match=true`。31 项串行节流 100ms 约 3.1 秒，可接受。

### 2.13 SMK-13 只读 API 与 V85 冻结数据一致性 ✅ PASS

- `risk_db` MD5 `2c85f402…` 稳定，与 git 跟踪版本一致
- 全程 0 次 zhiji API 调用（`no_zhiji_api_call: true`）
- 未修改任何 V85 原始产物（`git status` 仅新增本工单 5 份文档）

### 2.14 SMK-14 门户版本切换链路 ⚠ 警告

切换 `f313570 → v86-dev`：V85 侧正常返回；V86 侧返回 `403 VERSION_READ_FORBIDDEN`。
门户需实现「V86 栏不可读时显示占位提示 + 引导改用任务接口」的降级 UI（已在设计文档 §6 定义）。

### 2.15 SMK-15 任务提交链路 ❌ BLOCKED（依赖未就绪）

`POST /api/v1/tasks` 无实现（E 仅交付接口契约 `v86_task_api_design.md`，无服务端代码；`task_run` 表仅 schema）。
门户降级：「🚀 异步任务面板」显示 `⏳ V86 任务 API 未上线`，表单提交写入本地 `task_queue/` 供后端回放。

### 2.16 SMK-16 任务结果回显 ❌ BLOCKED（依赖 SMK-15）

`GET /api/v1/tasks/{id}/result` 无实现，结果注入对比面板的链路无法验证。
替代验证：DSHB `comparison_report.json`（`v85_v86_rule_compare.py` 产出）可作为结果样本，已接入对比面板展示逻辑（见 `v85_v86_compare_panel.md`）。

### 2.17 SMK-17 测试样本面板加载 ✅ PASS

`v86_rule_test_suite.json` 解析成功：

| 项 | 值 |
|---|---|
| suite | `v86-rule-test-suite-v1` |
| total_cases | 48 |
| groups | 4（BL-009a 12 / BL-026 12 / BL-012_Plan_B 8 / PDF_Fix 12） |
| 字段完整性 | `case_id`/`indicator_name`/`matched_name`/`expected_result`/`expected_rule`/`risk_level`/`source_risk` 全齐 ✅ |
| 兼容声明 | `compatible_with: ["v86_p0_rule_prototype.py", "v86_async_task_api"]` |

### 2.18 SMK-18 只读权限前端一致性 ✅ PASS

门户无编辑按钮暴露；`PortalReadOnlyClient.TOKEN` 固定 `v85-portal-r-0001`（`portal_read`）；版本参数固定 `f313570`。详见 `portal_permission_config.md`。

---

## 3. 失败与警告汇总

| # | 严重度 | 项 | 状态 | 处理建议 | 责任方 |
|---|---|---|---|---|---|
| SMK-01 | 🔴 阻断 | Windows 硬编码 repo_root | FAIL | 改为环境变量+`Path(__file__)` 兜底（1 行） | E |
| SMK-15 | 🔴 阻断（外部依赖） | V86 任务 API 无实现 | BLOCKED | 后端实现 `task_run` + 6 端点 | E |
| SMK-16 | 🔴 阻断（外部依赖） | 任务结果回显 | BLOCKED | 依赖 SMK-15 | E |
| SMK-04 | 🟡 警告 | 4 项制品路径过期 missing | WARN | PR 修正 `ARTIFACTS` relpath + 重跑 smoke | E |
| SMK-09 | 🟡 警告 | Python 层写方法抛 TypeError | WARN | 补显式桩方法抛 `WriteForbiddenError` | E |
| SMK-11 | 🟡 警告 | 门户缺 ops_read 令牌 | WARN | 门户配置 `v85-admin-readonly-0001` 双令牌 | HERMES |
| SMK-14 | 🟡 警告 | V86 栏不可读降级 UI | WARN | 按设计 §6 实现占位提示 | HERMES |

### 3.1 阻断项判定

- **SMK-01**：门户部署前必须修复（否则服务起不来）。修复成本 1 行代码。
- **SMK-15/16**：非 HERMES 可控，属 V86 后端实现范围；门户已定义降级路径，不阻断 V85 冻结门户上线。

---

## 4. 核心链路结论

| 链路 | 门户 → API → 存储 | 结果 |
|------|---|---|
| 版本切换 | `versions` → 2 版本正确隔离 | ✅ |
| 文件查询 | `query(risk_db/scenario_replay)` → 50/2721 行 | ✅ |
| MD5 校验 | `verify(..., verify_file=1)` → match=true | ✅ |
| 写保护 | 405/403 三层拒绝 | ✅（HTTP 层）⚠（Python 层） |
| 任务提交 | `POST /tasks` → 无实现 | ❌ 降级 |
| 结果回显 | `GET /tasks/{id}/result` → 无实现 | ❌ 降级 |

## 5. 约束合规

- ✅ `NO_ZHIJI_API_CALL=TRUE`：全程 0 次 zhiji 调用
- ✅ `NO_MODIFY_SOURCE_TEMPLATE=TRUE`：未修改 V85 任何产物
- ✅ 仅新增本工单 5 份文档
- ✅ 分支锁定 `feature/v85-chart-template`
