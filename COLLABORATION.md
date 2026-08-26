# framework-tree 项目协作机制

> 生成：2026-08-26
> 版本：v1（两条线隔离 + GitHub 状态同步）
> **任何参与本项目的 agent 先读本文档，再读 STATUS.md，再开工。**

---

## 一、项目概览

建设 8 品种（铜/铝/铅/锌/镍/锡/锂/硅）产业指标看板，复刻 metals-framework 形态。数据来自 Zhiji API。

---

## 二、两条线隔离（严禁串线）

| | 线A：架构 + GitHub | 线B：指标录入 + 数据整理 |
|---|---|---|
| **任务** | 前端页面、目录树 UI、API 服务器、ECharts 图表、GitHub 部署 | 同花顺 Prompt 调研、指标清单整理、zhiji_id 验证、数据库录入 |
| **写权限目录** | `/home/ubuntu/framework-tree/` | `/home/ubuntu/analysis/iwencai/`<br>`/home/ubuntu/analysis/spec/`<br>`/home/ubuntu/analysis/temp/` |
| **禁止写** | `/home/ubuntu/analysis/iwencai/`（线B专属） | `/home/ubuntu/framework-tree/`（线A专属，但可**通知**线A推 GitHub） |
| **交接文档** | `framework-tree/docs/handover_a.md` | `analysis/iwencai/handover_b.md` |
| **触发点** | 部署 / API / 图表 / 样式 | 指标清单 / 数据录入 / Prompt 迭代 |

**隔离原理**：文件锁白名单强制隔离（`~/.hermes/scripts/file_write_lock.py`）。线A agent 尝试写 `analysis/iwencai/` 会被拒，线B agent 尝试写 `framework-tree/` 会被拒。

---

## 三、协作流程（线B→线A 的推送链条）

```
① 线B 完成一个品种的数据整理
   （表单A/B填满 + zhiji_id 验证 + indicator_meta 入库）

② 线B 更新 STATUS.md
   （在 "B→A 待办" 区加一行：品种+完成项+需要的API改动）

③ 线B 通知线A（飞书/微信一句话）
   "铅库存数据已就绪，请接入 API + ECharts"

④ 线A 读取 STATUS.md → 接指标进 api_server.py → 推 GitHub → 更新 STATUS.md
```

**反过来（线A→线B）**：通常不需要。只有前端改版导致需要线B配合时，线A 在 STATUS.md "A→B 待办" 加一行并通知线B。

---

## 四、状态同步规则

| 规则 | 说明 |
|---|---|
| **单真源** | `framework-tree/STATUS.md` 是唯一状态记录，两个 agent 都只读/写这个文件 |
| **GitHub 可追溯** | STATUS.md 每次更新都要 `git commit + push`，保留完整历史 |
| **写完立即推** | 任何修改 STATUS.md 后 30 秒内必须 commit + push |
| **不重复写** | 两人不同时编辑 STATUS.md；拿到文件锁才写，写完释放 |
| **交接文档独立** | 各自的 handover_a/handover_b 只写自己的，不同步 |

---

## 五、给外部/新参与 agent 的指引

新 agent 进来后按这个顺序读：

```
1. README.md              ← 项目一句话 + 快速开始
2. STATUS.md              ← 当前进度 + 我负责什么
3. docs/handover_a.md     ← 线A(架构)交接文档
4. docs/handover_b.md     ← 线B(数据)交接文档
5. 确认自己属于哪条线 → 读对应 handover → 开工
```

**严禁跳步**：不读 STATUS.md 直接改代码 = 可能覆盖别人的工作。

---

## 六、Git 规范

| 线 | commit 前缀 | 示例 |
|---|---|---|
| 线A | `[A]` | `[A] feat: 接入铅库存 ECharts 四图` |
| 线B | `[B]` | `[B] data: 铅库存 zhiji_id 验证完成` |
| 文档 | `[DOC]` | `[DOC] update: STATUS.md 状态同步` |

Git push 命令：
```bash
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

---

## 七、技术要点（双方都需注意）

| 项 | 规则 |
|---|---|
| Zhiji 限频 | 本地 1 秒/次，批量拉数据必须 sleep 1s 间隔 |
| 反拷贝 | 前端禁用右键/Ctrl+C/S/P/F12/选中/拖拽 |
| SQLite DB | `api_cache.db` 不推 GitHub，只推代码和 JSON 配置 |
| 数据敏感 | 网页端无 CSV/Excel 导出，去除"合计"行 |