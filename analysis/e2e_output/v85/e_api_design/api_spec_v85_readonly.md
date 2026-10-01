# V85 只读制品访问接口规范

> 任务：`E_V85_READONLY_API_AND_V86_BACKEND_DESIGN` · T2.1
> 分支：`feature/v85-chart-template`
> 基线：HERMES `a2815c4` / DSHB `6771406` / DSHE `f313570`
> 实现：`v85_artifact_api.py`（同目录）
> API 版本：`v1` · Schema：`v1`
> 状态：**Frozen Read-Only**

---

## 1. 设计原则

| 原则 | 说明 |
|---|---|
| **只读** | 仅 `GET`。所有写入方法（POST/PUT/PATCH/DELETE）一律 `403 WRITE_FORBIDDEN` |
| **不联网** | 无 `requests`/`httpx`/`socket`/`subprocess`。不调用 zhiji API（`NO_ZHIJI_API_CALL=TRUE`） |
| **不改业务结果** | 仅对外暴露 V85 冻结版本已有的产物文件；不在服务期生成或改写数据 |
| **路径沙盒** | 所有访问必须命中 `ARTIFACTS` 白名单；`relpath` 越出 `analysis/e2e_output/v85/` 直接 403 |
| **版本可回溯** | 版本号、tag、commit、产出目录、MD5、字节数绑定固定注册表 |
| **可验证** | 每个制品返回 MD5 与字节数，客户端可自行 `verify_md5` 端点重算 |
| **分页强制** | 查询端点默认 `limit=100`，硬上限 `10000`；单响应 > 256 KiB 走"元数据 + 分页"降级 |

---

## 2. 版本注册表

V85 冻结基线以不可变注册表方式内嵌于 `v85_artifact_api.py`：

| key | version_tag | commit_sha | branch | output_root | readable |
|---|---|---|---|---|---|
| `f313570` | `v85.0` | `f3135709f1fd2c4ee8f972596ecde130e5128575` | `feature/v85-chart-template` | `analysis/e2e_output/v85` | ✅ |
| `v86-dev` | `v86-dev-placeholder` | – | `feature/v86-alias-engine` | `analysis/e2e_output/v86` | ❌ |

`v86-dev` 是占位符：`v86_init_backlog_total.md` 未就绪前不开放读服务，返回 `403 VERSION_READ_FORBIDDEN`。

**版本号解析顺序**（`resolve_version()`）：
1. 注册表 key 精确匹配（`f313570` / `v86-dev`）
2. `commit_sha` 完整/短哈希
3. `version_tag`（`v85.0`）
4. `branch` 名

---

## 3. 制品白名单

31 项制品按 6 组分类登记。所有 `relpath` 相对 `analysis/e2e_output/v85/`：

### 3.1 风险库
| kind | relpath | 类型 |
|---|---|---|
| `risk_db` | `unified_risk_db/unified_indicator_risk_db.csv` | csv |
| `risk_db_schema` | `unified_risk_db/risk_db_schema.md` | markdown |
| `risk_summary` | `unified_risk_db/unified_risk_summary_report.md` | markdown |

### 3.2 场景 A/B 回放
| kind | relpath | 类型 |
|---|---|---|
| `scenario_replay` | `dshb_full_integrate/full_488_template_playback_result.csv` | csv |
| `chart_risk_bound` | `v85_final_integrate/chart_risk_bound_all.json` | json |
| `cross_variety_p0` | `dshb_full_integrate/cross_variety_p0_validation.csv` | csv |

### 3.3 别名与冲突
| kind | relpath | 类型 |
|---|---|---|
| `alias_library` | `hermes_portal_gate_final/indicator_alias_library.csv` | csv |
| `alias_audit_sample` | `dshe_alias_audit_design/alias_audit_sample.csv` | csv |
| `multi_canonical_conflicts` | `dshe_alias_audit_design/multi_canonical_conflicts_165.csv` | csv |
| `alias_conflict_classification` | `dshe_alias_audit_design/multi_canonical_conflict_classification.csv` | csv |
| `alias_test_case_set` | `dshe_alias_audit_design/alias_test_case_set.json` | json |
| `ambiguous_indicator_list` | `hermes_portal_gate_final/ambiguous_indicator_list.csv` | csv |
| `high_risk_confusion_pairs` | `hermes_portal_gate_final/high_risk_confusion_pairs.csv` | csv |

### 3.4 模板清单
| kind | relpath | 类型 |
|---|---|---|
| `template_manifest` | `hermes_portal_gate_final/ths_render_task_manifest.json` | json |
| `template_task_list` | `hermes_portal_gate_final/ths_render_task_list.json` | json |
| `template_task_summary` | `hermes_portal_gate_final/ths_render_task_summary.csv` | csv |

### 3.5 黑名单 / Gate
| kind | relpath | 类型 |
|---|---|---|
| `blacklist_v85_final` | `dshb_full_integrate/semantic_blacklist_v85_final.json` | json |
| `blacklist_v85_fixed` | `unified_risk_db/semantic_blacklist_fixed.json` | json |
| `blacklist_change_log` | `dshb_full_integrate/blacklist_change_log.md` | markdown |
| `gate_config` | `dshe_alias_audit_design/regression_gate_config.json` | json |
| `blacklist_rule_test` | `dshe_alias_audit_design/blacklist_rule_test_result.json` | json |

### 3.6 设计文档
| kind | relpath | 类型 |
|---|---|---|
| `v86_engine_design` | `dshe_alias_audit_design/v86_alias_engine_full_design.md` | markdown |
| `v86_gate_fusion` | `dshe_alias_audit_design/v86_gate_fusion_framework.md` | markdown |
| `v85_delivery_manifest` | `hermes_v85_final_delivery/v85_full_delivery_manifest_v2.md` | markdown |
| `v85_delivery_readme` | `hermes_v85_final_delivery/v85_delivery_readme.md` | markdown |
| `v85_gate_acceptance` | `hermes_v85_final_delivery/v85_gate_final_acceptance_report.md` | markdown |
| `portal_v6_final` | `hermes_v85_final_delivery/enhanced_review_portal_v6_final.md` | markdown |
| `dshb_gate_summary` | `dshb_final_gate_summary/dsh_final_gate_acceptance.md` | markdown |
| `dshb_rule_summary` | `dshb_final_gate_summary/v85_rule_full_summary.md` | markdown |
| `dshb_v86_milestone` | `dshb_final_gate_summary/v86_rule_milestone_ticket.md` | markdown |
| `e_api_spec` | `e_api_design/api_spec_v85_readonly.md` | markdown |

未登记的路径一律 `404 ARTIFACT_NOT_REGISTERED`。**新增制品必须走 PR 修改 ARTIFACTS 表并跑 `--smoke`**。

---

## 4. 端点清单

### 4.1 `GET /api/v1/health`
- 角色：`portal_read`（默认放行，无 token 也可调用）
- 用途：探活、版本探测
- 返回：
```json
{
  "status": "ok",
  "api_schema": "v1",
  "version": "1.0.0",
  "task_id": "E_V85_READONLY_API_AND_V86_BACKEND_DESIGN",
  "read_only": true,
  "no_zhiji_api_call": true,
  "registered_versions": 2,
  "registered_artifacts": 31
}
```

### 4.2 `GET /api/v1/versions?include_inactive=0`
- 角色：`portal_read`
- 用途：列出可见版本；`include_inactive=1` 包含未开放读服务的占位版本（如 `v86-dev`）
- 返回：`{versions: [{key, version_tag, commit_sha, branch, frozen_at, output_root, writable, readable, upstream, notes}], count, read_only}`

### 4.3 `GET /api/v1/artifacts?version=f313570`
- 角色：`portal_read`
- 用途：列出白名单内全部制品 + 存在性 + 字节数
- 返回：`{version, commit_sha, artifacts: [{kind, relpath, content_type, description, exists, size_bytes}], count, read_only}`

### 4.4 `GET /api/v1/artifacts/{kind}?version=f313570`
- 角色：`portal_read`
- 用途：单制品元数据
- 返回：
```json
{
  "kind": "risk_db",
  "relpath": "unified_risk_db/unified_indicator_risk_db.csv",
  "content_type": "text/csv; charset=utf-8",
  "type": "csv",
  "description": "V85 统一指标风险数据库...",
  "keys": ["id", "risk_level", "template_id", "variety", "blacklist_id", "is_duplicate"],
  "filters": ["risk_level", "variety", "source", "blacklist_id", "risk_category", "conflict_type", "verify_status", "is_duplicate"],
  "version": "v85.0",
  "commit_sha": "f3135709f1fd2c4ee8f972596ecde130e5128575",
  "exists": true,
  "size_bytes": 11760,
  "md5": "819cb85aceef9d859b7792302de7b890",
  "last_modified": "2026-10-01T16:20:00+08:00"
}
```

### 4.5 `GET /api/v1/artifacts/{kind}/query?limit=&offset=&filters=&sort=&reverse=&version=`
- 角色：`portal_read`
- 用途：分页查询（csv/json 制品）
- 参数：
  - `limit`：`1..10000`（默认 100）
  - `offset`：`>=0`（默认 0）
  - `filters`：JSON 对象；简单形式 `{"field": "value"}` 等价于 `{"op":"eq"}`；复杂形式 `{"field": {"op": "eq|ne|in|contains|regex|lt|le|gt|ge", "value": ...}}`
  - `sort`：字段名（仅允许 `[A-Za-z_][A-Za-z0-9_]*`）
  - `reverse`：`1|true`（默认 `0`）
- 过滤字段受白名单约束（`ARTIFACTS[kind].filters`）；超出白名单 → `400 FILTER_NOT_ALLOWED`
- 返回：
```json
{
  "kind": "risk_db",
  "version": "v85.0",
  "commit_sha": "f313570...",
  "total": 500,
  "filtered": 244,
  "offset": 0,
  "limit": 100,
  "returned": 100,
  "next_offset": 100,
  "filters": {"risk_level": "P0"},
  "sort": null,
  "rows": [...],
  "read_only": true
}
```

### 4.6 `GET /api/v1/artifacts/{kind}/file?version=`
- 角色：`portal_read`
- 用途：小文件整文件下载（≤ 256 KiB）；大文件只返回元数据 + MD5，客户端改用 `/query`
- 返回：
  - **≤ 256 KiB**：`{kind, relpath, version, size_bytes, md5, content_type, content, encoding, read_only}`
    - csv/markdown：`content` 为 UTF-8 字符串
    - json：`content` 为解析后的对象
    - 其他：`content_b64`（Base64）
  - **> 256 KiB**：`{..., content: null, content_note: "文件 > 256 KiB，仅提供元数据；请调用 query() 端点分页读取。"}`

### 4.7 `GET /api/v1/artifacts/{kind}/verify?expected_md5=<32hex>&verify_file=1&version=`
- 角色：`portal_read`
- 用途：MD5 校验（客户端提交期望值，服务端比对）
- `verify_file=1`：从磁盘实时重算（缓存旁路），用于跨机器校验
- 返回：
```json
{
  "kind": "risk_db",
  "version": "v85.0",
  "expected_md5": "819cb85aceef9d859b7792302de7b890",
  "actual_md5": "819cb85aceef9d859b7792302de7b890",
  "match": true,
  "verified_from_cache": false,
  "commit_sha": "f313570..."
}
```

### 4.8 `GET /api/v1/audit?version=`
- 角色：`audit_read`
- 用途：审计视图——所有登记制品的存在性 + MD5 + 字节数（含 `e_api_design` 自身）
- 返回：`{version, commit_sha, rows: [{kind, relpath, exists, size_bytes, md5}], count, read_only}`

### 4.9 `GET /api/v1/metrics`
- 角色：`ops_read`
- 用途：运维指标（API 版本、注册计数、60 秒内请求数、缓存命中率）

---

## 5. 权限模型

### 5.1 角色
| 角色 | 允许动作 |
|---|---|
| `portal_read` | `list_versions` / `get_artifact_meta` / `query` / `get_file` / `verify_md5` / `health` |
| `audit_read` | `portal_read` + `list_audit` |
| `ops_read` | `health` / `metrics` |
| `portal_write` | **空**（显式禁止；用于验证写保护） |

### 5.2 令牌示例（内嵌 TOKENS 表）
| Token | 角色 |
|---|---|
| `v85-portal-r-0001` | `portal_read` |
| `v85-reviewer-r-0001` | `portal_read, audit_read` |
| `v85-admin-readonly-0001` | `portal_read, audit_read, ops_read` |
| `v85-portal-w-0001` | `portal_write`（永拒） |

生产环境替换为 JWT + 白名单 + 过期时间。当前硬编码仅示范接口骨架。

### 5.3 错误响应
统一错误格式：
```json
{
  "error": true,
  "code": "ROLE_FORBIDDEN",
  "message": "角色 'audit_read' 不在令牌权限集 ['portal_read']",
  "detail": {"token_prefix": "v85-portal", "required": "audit_read"},
  "timestamp": "2026-10-01T16:20:00+08:00"
}
```

| 状态码 | 错误码 | 说明 |
|---|---|---|
| 400 | `BAD_MD5_FORMAT` / `BAD_LIMIT` / `BAD_OFFSET` / `BAD_SORT` / `BAD_SORT_KEY` / `BAD_OP` / `FILTERS_TOO_MANY` / `FILTER_NOT_ALLOWED` / `MISSING_MD5` / `QUERY_NOT_SUPPORTED` | 参数校验失败 |
| 401 | `NO_TOKEN` / `BAD_TOKEN` | 认证失败 |
| 403 | `ROLE_FORBIDDEN` / `VERSION_READ_FORBIDDEN` / `VERSION_WRITABLE` / `PATH_ESCAPE` / `WRITE_FORBIDDEN` | 权限/版本/路径策略拒绝 |
| 404 | `VERSION_NOT_FOUND` / `ARTIFACT_NOT_REGISTERED` / `ARTIFACT_FILE_MISSING` / `ROUTE_NOT_FOUND` | 目标不存在 |
| 405 | `METHOD_NOT_ALLOWED` | 非 GET 方法 |
| 422 | `MD5_MISMATCH` | 校验值不匹配（`verify_file=1` 时通过响应体返回 `match:false` 而非抛 422，便于客户端批量诊断） |
| 429 | `RATE_LIMIT` | 60 秒 > 300 次 |

---

## 6. 写保护

三重防线：

1. **HTTP 层**：`dispatch()` 检测 `method ∈ {POST, PUT, PATCH, DELETE, TRACE, CONNECT, OPTIONS}` → 405 `METHOD_NOT_ALLOWED`（在路由前）
2. **API 层**：所有写方法 `put/post/patch/delete` 直接抛 `WriteForbiddenError` → 403 `WRITE_FORBIDDEN`
3. **版本层**：`resolve_version()` 检测 `writable=True` 直接抛 `VERSION_WRITABLE`

响应体显式提示替代方案（"调用 GET /api/v1/versions 查询版本"），避免调用方继续试写。

---

## 7. 速率限制

- 60 秒滚动窗口
- 默认 300 次/分钟（全局计数器，进程内）
- 生产环境应替换为 Redis Token Bucket 或网关限流

---

## 8. 部署与集成

### 8.1 独立进程内调用（推荐用于评审门户后端）
```python
from v85_artifact_api import ArtifactAPI, ApiError
api = ArtifactAPI(repo_root="D:/DSH_WORK/framework-tree", token="v85-portal-r-0001")
try:
    meta = api.get_artifact_meta("risk_db", version="f313570")
    print(meta["md5"], meta["size_bytes"])
except ApiError as e:
    print(e.to_dict())
```

### 8.2 FastAPI 适配（示意，不随交付物发布）
```python
from fastapi import FastAPI, Header, HTTPException
app = FastAPI()
api = ArtifactAPI(repo_root=os.environ["FRAMEWORK_TREE"], token=None)

@app.get("/api/v1/artifacts/{kind}")
async def get(kind: str, token: str = Header(alias="Authorization")):
    # 生产应在此校验 token；此处省略
    try:
        return api.get_artifact_meta(kind)
    except ApiError as e:
        raise HTTPException(status_code=e.status, detail=e.to_dict())
```

### 8.3 命令行自检
```bash
python v85_artifact_api.py --smoke        # 冒烟测试
python v85_artifact_api.py --list-artifacts
python v85_artifact_api.py --meta risk_db
```

---

## 9. 与评审门户集成

门户调用示例（P0 拦截率统计）：
```python
# 拉 P0 计数
q = api.query("risk_db", filters={"risk_level": "P0"}, limit=10000)
p0_count = q["filtered"]

# 拉黑名单命中分布
hits = {}
for row in q["rows"]:
    hits[row.get("blacklist_id") or "(none)"] = hits.get(row.get("blacklist_id") or "(none)") + 1

# 交叉验证：MD5 校验
verify = api.verify_artifact_md5("risk_db", expected_md5="...", verify_file=True)
assert verify["match"], f"risk_db 已被篡改: {verify}"
```

---

## 10. 未覆盖事项（明确非目标）

1. **无 WebSocket / 长轮询**：V85 冻结，无需推送。
2. **无鉴权中间件抽象**：TOKENS 表可替换为 JWT，但框架不预设。
3. **无文件下载流式响应**：文件 ≤ 256 KiB 一次返回，> 256 KiB 强制分页。
4. **无跨版本 diff 端点**：V85→V86 对比见 `v85_to_v86_migration_verify_plan.md`。
5. **无任务调度**：V86 异步任务见 `v86_task_api_design.md`。
6. **无数据库持久化**：所有元数据内存中构建，服务重启不丢失（因为文件在磁盘）。
7. **不替代 git**：版本回溯通过 `commit_sha` 字段完成，不提供 git log 查询。

---

## 11. 交付与验收

- 代码：`v85_artifact_api.py`（约 1000 行，标准库零依赖）
- 冒烟：`python v85_artifact_api.py --smoke` → `PASS`（覆盖：健康/版本/元数据/MD5 校验/查询/写保护/路由/权限）
- 约束：`NO_ZHIJI_API_CALL=TRUE` / `READ_ONLY=TRUE` / `NO_MODIFY_SOURCE=TRUE` / `NO_GT_MODIFICATION=TRUE`
- 制品白名单：31 项（详见 §3）
- 角色白名单：4 项（详见 §5.1）
- 端点：9 个（详见 §4）
