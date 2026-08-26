# 给线B（指标录入/数据整理）的迁移指南

> 由线A编写，供线B参考。
> **原则：你可以随时按自己的节奏执行，不影响你当前的工作。**
> 迁移前、迁移中、迁移后，你的数据都不会丢失。

---

## 你（线B）当前应该知道的

### 1. 目录划分（从2026-08-26起生效）

| 你管（写） | 线A管（你只读） |
|---|---|
| `/home/ubuntu/analysis/iwencai/` | `/home/ubuntu/framework-tree/` |
| `/home/ubuntu/analysis/spec/` | |
| `/home/ubuntu/analysis/temp/` | |

**你的数据产物（表单、zhiji_id验证结果、灌库脚本）请写上面左边目录，不要写 framework-tree/。**

### 2. 之前你写在 framework-tree/ 的文件——没有丢

`pb_stock.html` / `build_pb_stock.py` / `pb_stock_demo.html` / `render_demo.py` / `assets/echarts.min.js` 还在，线A按你的要求保留了。

**建议**：这些文件属于数据/指标工作，建议你**下次有空时**复制到 `analysis/iwencai/PB/` 下备份。线A这边不动。

---

## 统一 ID 映射（重要）

线A和线B 之前各维护一份 Zhiji ID（api_server.py 和 data_layer.py 用的是不同的 ID，同一个"社库"对不上）。

**现在统一到一个文件**：`framework-tree/data/indicators_v1.json`

结构示例：
```json
"社库": {
  "name": "社会库存",
  "unit": "万吨",
  "freq": "weekly",
  "verified": false,     ← false=占位，true=你已验证
  "ids": {"PB": "ID00188315", "ZN": "ID00188329", ...}
}
```

**你验证 zhiji_id 后，更新这个 JSON**（把 verified 改成 true，替换正确的 ID）。
线A会从这里读，你改完 git push 后线A自然用上——**不用再找线A改代码**。

---

## 协作节奏

| 你的动作 | 线A 会做什么 |
|---|---|
| 完成一个品种的 zhiji_id 验证 + 更新 indicators_v1.json + push | 读 JSON 生效，无需通知 |
| 完成一个品种的灌库（indicator_meta 写入） | 按 STATUS.md "B→A 待办" 接 ECharts |
| 需要线A帮忙改前端 | 在 STATUS.md "B→A 待办" 加一行，通知我 |

---

## 一句话总结

> 你的数据放 `analysis/iwencai/`，zhiji_id 统一写到 `indicators_v1.json`，状态同步看 `STATUS.md`，其余不用管线A。

有疑问找线A。