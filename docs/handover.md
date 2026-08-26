# 交接文档 · 有色金属产业指标树

> 生成时间：2026-08-26  
> 状态：目录树前端已上线，图表待接入

## 已完成
- [x] GitHub 仓库创建：`algo23-yunqingtian/framework-tree`
- [x] GitHub Pages 上线：https://algo23-yunqingtian.github.io/framework-tree/
- [x] 目录树完全复刻 metals-framework 形态
  - 7 大类 × 33 指标叶 × 258 品种 chip
  - 叶行右侧挂彩色品种 chip（和 amiya 一致）
  - 浅米色主题，编号+名称+问题描述
- [x] 配置内联进 HTML（消除 GitHub Pages JSON fetch 问题）
- [x] 数据层骨架 `scripts/data_layer.py`（SQLite + Zhiji 增量）
- [x] 交接文档 + 架构文档同步推 GitHub

## 待做
- [ ] 与同花顺确认各品种核心指标清单（当前为占位 ID）
- [ ] 接入 ECharts 图表（替换占位面板）
- [ ] 配置 cron 每日增量更新
- [ ] 启动本机 Flask/FastAPI 提供 `/api/indicator` 接口
- [ ] 铜/铝/铅/锡/锂/硅 6 品种的同花顺对话

## 关键技术点
1. **不要重新拉取数据给页面**——页面只读本地 SQLite
2. **Zhiji 无额度，只有 1 秒限频**——cron 跑再快也不会浪费
3. **数据 ID 待验证**——当前 `data_layer.py` 中的 Zhiji ID 是占位符，正式使用前必须 `search → series` 逐一验证
4. **Git push 超时常见**——用 `GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10"` 可解决

## 本地关键路径
| 路径 | 用途 |
|---|---|
| `/home/ubuntu/framework-tree/` | 项目根目录（GitHub 同步） |
| `/home/ubuntu/.hermes/scripts/zhiji_api.py` | Zhiji API 客户端 |
| `/home/ubuntu/analysis/handover_indicatortree_20260826.md` | 原始交接文档 |
| `/home/ubuntu/analysis/frame/*.md` | 品种框架文件 |
| `/home/ubuntu/analysis/temp/iwencai_*.md` | 同花顺对话记录（锌已做） |

## 给后续 Agent 的启动顺序
1. 读 `docs/architecture.md` 了解数据流
2. 改 `data/tree_config.json` 调整目录树（记得同步 HTML 内联部分）
3. 改 `scripts/data_layer.py` 的指标 ID 映射
4. 跑 `data_layer.py full` 验证数据
5. 在前端替换占位面板为 ECharts 图表
