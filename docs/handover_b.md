# 交接文档 · 线B：指标录入 + 数据整理

> 更新：2026-08-26
> 版本：v1（协作机制上线）
> 负责：同花顺 Prompt 调研、指标清单整理、zhiji_id 验证、数据库录入
> **本文件供线B读取。线A也能看到，但线B是主导者。**

---

## 一、你（线B）的写权限范围

**允许写**：
- `/home/ubuntu/analysis/iwencai/`（品种调研结果）
- `/home/ubuntu/analysis/spec/`（Prompt 框架 / 数据库设计）
- `/home/ubuntu/analysis/temp/`（临时对话记录）

**禁止写**（属线A）：
- `/home/ubuntu/framework-tree/`（架构/前端/GitHub 部署）

> ⚠️ 如果你需要改动前端或推 GitHub，**不要自己写 framework-tree/**。
> 改在 STATUS.md "B→A 待办"加一行，然后通知线A来做。

---

## 二、协作规则（开工前必读 STATUS.md）

| 规则 | 说明 |
|---|---|
| 开工前 | 先读 `framework-tree/STATUS.md`，看有无 A→B 待办 |
| 数据就绪 | 在 STATUS.md "B→A 待办"加一行（品种+完成项+所需API改动） |
| 通知线A | 在 STATUS.md 加完待办后，飞书/微信一句话通知线A |
| 不直接推 GitHub | 前端/仓库更新由线A负责，你只通知 |
| commit 前缀 | 你正常提交自己目录的代码用 `[B]`（如果有 git 仓库） |

---

## 三、STATUS.md 是唯一同步真源

`framework-tree/STATUS.md` 是**两个线都能读和写**的共享日志：
- 你读它：看线A有没有留给你的事
- 你写它：告诉线A你的进度、需要什么
- 线A读/写它：回你进度

**它放在 `framework-tree/` 下，但你作为线B有**读**权限**——这条规则在 `COLLABORATION.md` 里明确。

---

## 四、已完成工作

| 产物 | 路径 |
|---|---|
| 同花顺批量 Prompt v3 | `/home/ubuntu/analysis/spec/iwencai_batch_prompt_v3.md` |
| 数据库设计（indicator_meta/series 两表） | `/home/ubuntu/analysis/spec/db_design.md` |
| 铅库存实测返回 | `/home/ubuntu/analysis/iwencai/PB/stock_raw_v4.md` |

---

## 五、待做（按优先级）

| # | 任务 | 说明 |
|---|---|---|
| 1 | 铅库存 zhiji_id 验证 | 对 stock_raw_v4 的19个指标 search→series 逐一验证 |
| 2 | 铅库存灌库 | 建 indicator_meta/indicator_series，灌入验证后的数据 |
| 3 | 其余7品种调研 | 铜/铝/镍/锡/锂/硅，复用 Prompt v4 |
| 4 | 通知线A接API | 每完成一个品种，STATUS.md 记一行 + 通知线A |

---

## 六、你之前写过但误放进 framework-tree/ 的文件

以下 3 个文件目前在 `framework-tree/` 仓库里（由线A暂时保留）：
- `pb_stock.html` — 铅库存看板 HTML
- `build_pb_stock.py` — 铅库存看板生成脚本
- `assets/echarts.min.js` — 本地 ECharts

**以后这类产物请写到 `analysis/iwencai/` 下**，不要写 framework-tree/。线A后续接入正式 ECharts 时会自然处理这些临时文件。

---

## 七、新对话第一句话

> 读取 `/home/ubuntu/framework-tree/STATUS.md`（协作机制+当前状态），再读取 `/home/ubuntu/framework-tree/docs/handover_b.md`，继续品种指标树线B工作（指标录入/数据整理）。