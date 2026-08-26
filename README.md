# 有色金属产业指标树 · Metals Framework

复刻 [metals-framework](https://amiya866.github.io/metals-framework/#/tree) 形态的 8 品种产业指标看板。数据来自 Zhiji API，前端为 Dark ECharts 高密度独立页面。

## 🚨 新参与 Agent 必读（按顺序）

| 顺序 | 文件 | 读它干什么 |
|---|---|---|
| 1️⃣ | `README.md` | 你在读这个 |
| 2️⃣ | `COLLABORATION.md` | 项目协作机制：**两条线隔离、怎么交接、Git 规范** |
| 3️⃣ | `STATUS.md` | **当前进度**——你负责什么、谁在等谁 |
| 4️⃣ | `docs/handover_a.md` | 如果你是**线A（架构/前端）**，读这个开工 |
| 4️⃣ | `analysis/iwencai/handover_b.md` | 如果你是**线B（指标/数据）**，读这个开工 |

**严禁跳步。** 不读 STATUS.md 直接改代码 = 可能覆盖别人的工作。

---

## 两条线分工

```
线A：架构 + GitHub + 前端
├── 目录树 UI / ECharts 图表 / API 服务器
├── 写目录：/home/ubuntu/framework-tree/
└── 交接：docs/handover_a.md

线B：指标录入 + 数据整理
├── 同花顺 Prompt / zhiji_id 验证 / 数据库录入
├── 写目录：/home/ubuntu/analysis/iwencai/
└── 交接：analysis/iwencai/handover_b.md
```

> 两条线通过 `STATUS.md` 做状态同步（GitHub 可追溯），严禁串线。
> 详情见 `COLLABORATION.md`。

---

## 项目结构

```
framework-tree/
├── index.html              # 前端单页（目录树+看板，配置已内联）
├── data/tree_config.json   # 目录树配置（品种/大类/指标）
├── scripts/
│   ├── api_server.py       # Flask API + 3天滑动缓存（本地:8786）
│   └── data_layer.py       # 备用数据层
├── docs/
│   ├── architecture.md     # 数据架构设计
│   └── handover_a.md       # 线A交接文档
├── COLLABORATION.md        # 协作机制（必读）
├── STATUS.md               # 全局状态（必读）
└── README.md               # 本文件
```

## 在线地址

- **GitHub Pages**: https://algo23-yunqingtian.github.io/framework-tree/
- **源码**: https://github.com/algo23-yunqingtian/framework-tree

## 覆盖品种

铜(CU) · 铝(AL) · 铅(PB) · 锌(ZN) · 镍(NI) · 锡(SN) · 碳酸锂(LC) · 工业硅(SI)

## 本地启动

```bash
python3 /home/ubuntu/framework-tree/scripts/api_server.py 8786
# 浏览器访问 http://127.0.0.1:8786
```

## 技术要点

- Zhiji 无月度配额，仅 1 秒/次限频
- SQLite 缓存 DB（`api_cache.db`）不推 GitHub
- 反拷贝保护：禁用右键/Ctrl+C/S/P/F12/选中/拖拽
- 无 CSV/Excel 导出，去除"合计"行