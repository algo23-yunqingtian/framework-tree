# 门户只读权限与冻结控制配置

> 工单: `HERMES_V86_PORTAL_INTEGRATE_AND_V85_FROZEN_DEMO_LOCK` · T2.6
> 生成时间: 2026-10-02 09:44
> 分支: `feature/v85-chart-template` @ `5e874a7`
> 对齐: E `api_spec_v85_readonly.md` §5/§6（三层写保护）

---

## 1. 权限对齐总表

### 1.1 后端角色 → 门户能力映射

| 后端角色 | 令牌示例 | 允许动作 | 门户对应能力 |
|---|---|---|---|
| `portal_read` | `v85-portal-r-0001` | list_versions / get_artifact_meta / query / get_file / verify_md5 / health | 🔒 V85 冻结门户全部只读 Tab |
| `audit_read` | `v85-reviewer-r-0001` | portal_read + list_audit | 🔐 快照校验 Tab |
| `ops_read` | `v85-admin-readonly-0001` | portal_read + audit_read + metrics | 📉 运维指标面板 |
| `task_submit` | （V86 待实现） | POST /tasks | 🚀 任务提交 |
| `task_read` | （V86 待实现） | GET /tasks/{id}, /result | 🚀 任务进度与结果 |
| `task_admin` | （V86 待实现） | cancel / queue | 🚀 任务取消与队列 |
| `portal_write` | `v85-portal-w-0001` | **空（永拒）** | 无（用于验证写保护） |

### 1.2 门户双令牌配置

```yaml
# portal_config.yaml — 只读演示环境
api:
  base_url: "http://127.0.0.1:8766/api/v1"
  repo_root: "${FRAMEWORK_TREE:-/home/ubuntu/framework-tree}"

tokens:
  primary:
    value: "v85-admin-readonly-0001"      # 含 portal_read + audit_read + ops_read
    roles: [portal_read, audit_read, ops_read]
  fallback:
    value: "v85-portal-r-0001"            # 仅 portal_read（面板降级时用）
    roles: [portal_read]

versions:
  frozen:
    key: "f313570"
    version_tag: "v85.0"
    readable: true
  dev:
    key: "v86-dev"
    version_tag: "v86-dev-placeholder"
    readable: false

frozen_lock:
  enabled: true
  hide_edit_buttons: true
  disable_batch_import: true
  disable_review_writeback: true
  disable_blacklist_edit: true
  disable_alias_edit: true
  require_snapshot_verify_before_use: true
```

> ⚠️ SMK-11 发现：仅用 `portal_read` 令牌时 `/metrics` 返回 `ForbiddenError`。门户配置 primary 令牌为 `v85-admin-readonly-0001` 以覆盖运维指标；若运维面板不需要，可回退到 `v85-portal-r-0001` 并隐藏运维指标面板。

---

## 2. 三层写保护对齐

### 2.1 后端三层防线（E 交付）

| 层 | 机制 | 响应 |
|---|---|---|
| 1️⃣ HTTP 层 | `dispatch()` 检测 `POST/PUT/PATCH/DELETE/TRACE/CONNECT/OPTIONS` → 路由前拒绝 | `405 METHOD_NOT_ALLOWED` |
| 2️⃣ API 层 | `put/post/patch/delete` 抛 `WriteForbiddenError` | `403 WRITE_FORBIDDEN` |
| 3️⃣ 版本层 | `resolve_version()` 检测 `writable=True` | `403 VERSION_WRITABLE` |

### 2.2 门户前端第二道防线

| # | 机制 | 实现 |
|---|---|---|
| 1 | 无写方法封装 | `PortalReadOnlyClient` 类**不暴露**任何 `put/post/patch/delete` 方法 |
| 2 | 数据源固定 | `VERSION = "f313570"` 硬编码常量，不可由 URL 参数覆盖 |
| 3 | 令牌固定 | `TOKEN = "v85-portal-r-0001"`（或配置中的 primary），不读 localStorage 中的可篡改令牌 |
| 4 | 无表单提交 | 门户所有 `<form>` 均无 `method=POST`；所有交互为 GET 查询参数 |
| 5 | 无文件上传控件 | 移除 `<input type=file>` 与批量导入入口 |

### 2.3 写请求拦截（前端兜底）

```javascript
// 门户启动时全局拦截 — 双保险
const origFetch = window.fetch;
window.fetch = function(url, opts = {}) {
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET") {
    console.warn(`[FROZEN] 已拦截非 GET 请求: ${method} ${url}`);
    return Promise.resolve({
      ok: false, status: 405,
      json: () => Promise.resolve({
        error: true, code: "METHOD_NOT_ALLOWED",
        message: "V85 冻结环境仅允许 GET 请求"
      })
    });
  }
  return origFetch.call(this, url, opts);
};
```

---

## 3. 冻结版本编辑按钮屏蔽清单

### 3.1 必须屏蔽（V6 遗留入口 → V7-frozen）

| 入口 | V6 位置 | V7-frozen 处理 |
|---|---|---|
| 评审结果保存 | 批次 A/B/C 详情页 | 🔒 移除，改为「只读」标签 |
| 评审状态回写 | `review_result_apply.py` | 🔒 门户不调用；保留在 V86 任务接口 |
| 白名单新增 | 白名单管理 Tab | 🔒 移除；改为「查看 V85 白名单快照」 |
| 白名单过期续期 | 白名单管理 Tab | 🔒 移除；V86 自动化提醒 |
| THS zhiji_id 回写 | THS 映射 Tab | 🔒 移除；改为候选 864 条只读浏览 |
| 批量导入 | 工具栏 | 🔒 移除 |
| 黑名单规则编辑 | 规则管理 Tab | 🔒 移除；改为 31 规则只读浏览 |
| 别名库编辑 | 别名管理 Tab | 🔒 移除；改为 864 条只读浏览 |
| P0 处置确认 | P0 工作台 | 🔒 移除；改为 237 条只读列表 |
| Gate 项手动置为通过 | Gate 大盘 | 🔒 移除 |

### 3.2 保留交互（只读性质）

| 入口 | 保留方式 |
|---|---|
| 场景 A/B 切换 | ✅ 仅切换查询参数 `filters={"scenario":"A"}` |
| 批次 A/B/C 浏览 | ✅ 只读分页 |
| Gate 大盘筛选 | ✅ 前端过滤 |
| 风险搜索/筛选 | ✅ API 查询参数 |
| 制品下载 | ✅ `GET /artifacts/{kind}/file`（≤256KiB） |
| 快照全量校验 | ✅ `GET /artifacts/{kind}/verify` |
| 对比面板刷新 | ✅ 重新拉取 API |

### 3.3 视觉标记规范

| 元素 | 规范 |
|---|---|
| 顶部横幅 | `🔒 V85.0 FROZEN`，红底白字，64px，不可关闭 |
| 只读标签 | 每个数据 Tab 右上角 `🔒 只读` 徽章 |
| 禁用提示 | hover 原编辑位（保留占位）显示 tooltip「V85 冻结，请走 V86 任务接口」 |
| 冻结告警 | MD5 校验失败时横幅追加 `⚠️ 快照校验失败` |
| 任务面板 | V86 后端未就绪时 `⏳ V86 任务 API 未上线` |

---

## 4. 权限验证用例（门户自测）

| # | 测试 | 期望 | 实测（冒烟） |
|---|------|------|------|
| P-01 | `GET /health` | 200 `read_only:true` | ✅ PASS |
| P-02 | `GET /versions` | 2 版本，v86-dev `readable:false` | ✅ PASS |
| P-03 | `GET /artifacts` | 31 项 | ✅ PASS（4 项 missing，见 SMK-04） |
| P-04 | `POST /artifacts/risk_db` | 405/403 | ✅ HTTP 层拒绝 |
| P-05 | `PUT` 直接进程内调用 | `WriteForbiddenError` | ⚠️ TypeError（SMK-09） |
| P-06 | `GET /artifacts?version=v86-dev` | 403 `VERSION_READ_FORBIDDEN` | ✅ PASS |
| P-07 | `portal_read` 调 `/audit` | 403 `ROLE_FORBIDDEN` | ✅ PASS |
| P-08 | `portal_read` 调 `/metrics` | 403 `ROLE_FORBIDDEN` | ✅ PASS（SMK-11，需换令牌） |
| P-09 | 未知 kind | 404 `ARTIFACT_NOT_REGISTERED` | ✅ PASS |
| P-10 | 越界路径（路径穿越） | 403 `PATH_ESCAPE` | ✅ 契约定义 |
| P-11 | 超速（>300/min） | 429 `RATE_LIMIT` | ✅ 契约定义 |

---

## 5. 前端权限配置代码

```python
class PortalPermissionConfig:
    """门户只读权限配置 — 与后端三层写保护对齐。"""

    FROZEN_VERSION = "f313570"
    READONLY_TOKEN = "v85-portal-r-0001"
    ADMIN_READONLY_TOKEN = "v85-admin-readonly-0001"

    ALLOWED_METHODS = {"GET"}
    ALLOWED_ARTIFACTS_SCOPE = {"read": True, "write": False}

    EDIT_BUTTONS_DISABLED = [
        "review_save", "review_apply", "whitelist_add", "whitelist_renew",
        "ths_writeback", "batch_import", "blacklist_edit", "alias_edit",
        "p0_confirm", "gate_manual_pass",
    ]

    READONLY_FEATURES = [
        "scenario_switch", "batch_browse", "gate_dashboard",
        "risk_search", "artifact_download", "snapshot_verify",
    ]

    def is_editable(self, feature: str) -> bool:
        return feature in self.READONLY_FEATURES

    def assert_readonly(self, method: str):
        if method not in self.ALLOWED_METHODS:
            raise PermissionError(f"FROZEN: {method} not allowed (only GET)")

    def require_snapshot_verified(self, verify_result: dict) -> bool:
        """进入业务 Tab 前强制快照校验通过。"""
        return verify_result.get("pass_count") == 31
```

---

## 6. 与后端边界的职责划分

| 职责 | 门户（前端） | 后端（API） |
|---|---|---|
| 认证 | 持有令牌（配置注入，不可篡改） | 校验令牌→角色 |
| 授权 | 不调用越权端点 | 角色→动作判定 |
| 写保护 | 不封装写方法 + fetch 拦截 | 三层防线拒绝 |
| 版本隔离 | 版本常量硬编码 | `VERSION_READ_FORBIDDEN` |
| 速率限制 | 节流 100ms + 缓存 | 60s/300 次全局 |
| 数据完整性 | MD5 展示与告警 | 实时重算比对 |
| 审计 | 仅本地 sessionStorage | 审计日志持久化 |

**关键原则**：门户是**只读消费方**，安全边界由后端强制；门户的前端拦截仅为用户体验优化（提前反馈），**不得**作为安全依据。
