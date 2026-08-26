# 有色金属产业指标树 · Metals Framework

多品种（8品种）产业指标目录树 + 看板体系。数据结构完全复刻 [metals-framework](https://amiya866.github.io/metals-framework/#/tree) 形态：**大类 → 指标叶(编号+名称+问题) → 叶行右侧挂品种 chip**。

## 在线地址
- **GitHub Pages**: https://algo23-yunqingtian.github.io/framework-tree/
- **源码仓库**: https://github.com/algo23-yunqingtian/framework-tree

## 覆盖品种（8个）
| 代码 | 品种 | 代码 | 品种 |
|---|---|---|---|
| CU | 铜 | SN | 锡 |
| AL | 铝 | LC | 锂 |
| PB | 铅 | SI | 硅 |
| ZN | 锌 | NI | 镍 |

## 目录结构
```
framework-tree/
├── index.html              # 前端单页（目录树+看板，配置已内联）
├── data/tree_config.json   # 目录树配置（品种/大类/指标）
├── scripts/data_layer.py   # 数据层（SQLite + Zhiji 增量拉取）
├── docs/
│   ├── handover.md         # 交接文档
│   └── architecture.md     # 数据架构设计
└── README.md               # 本文件
```

## 快速开始
1. **前端**：直接部署到 GitHub Pages，`index.html` 已含全部逻辑
2. **数据层**：`python3 scripts/data_layer.py full` 首次全量拉取
3. **每日增量**：cron 定时跑 `python3 scripts/data_layer.py inc`

## 给其他 Agent 的运行规则
- 前端配置已内联进 `index.html`，改目录树需同时改 HTML 内联部分 + `tree_config.json`
- 数据源：Zhiji API（三合一，1秒限频，无月度配额）
- 数据存储：本地 SQLite（`indicators.db`），不推 GitHub
- 页面访问零配额消耗（只读本地），每天 cron 增量更新
- 反拷贝保护：已禁用右键/Ctrl+C/F12
