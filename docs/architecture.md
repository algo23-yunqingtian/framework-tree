# 数据架构设计 · framework-tree

## 一句话
**本地 SQLite 缓存 + Zhiji API 每日增量**。页面访问永远只读本地，零配额消耗。

## 数据流
```
Zhiji API ──(每日增量)──→ indicators.db (SQLite) ──(页面访问)──→ ECharts 渲染
```

## 为什么要本地缓存
1. Zhiji 有 1 秒限频，不是额度限制，但并发访问会挤爆
2. 用户打开页面时调用 API，100 人同时看 = 100 次调用，浪费且卡
3. 本地读 SQLite 是毫秒级，用户体验远好于实时调 API

## 为什么不会浪费"额度"
**Zhiji 没有月度/日度配额**，只有"同一服务两次真实调用间隔 ≥ 1 秒"的速度限制。
- 每天 cron 增量 120 个指标 = 120 秒 = 2 分钟
- 一天之内无论多少人访问页面，API 调用 = 0

## 数据量估算
| 项目 | 估算 |
|---|---|
| 独立数据系列 | ~80-120 个 |
| 3年历史总行数 | ~94,000 行 |
| SQLite 文件大小 | ~10-15 MB |

## 数据层命令
| 命令 | 用途 | 耗时 |
|---|---|---|
| `python3 scripts/data_layer.py full` | 首次全量拉取 | ~2 分钟 |
| `python3 scripts/data_layer.py inc` | 每日增量更新 | ~2 分钟 |
| `python3 scripts/data_layer.py status` | 查看各指标数据量 | 即时 |
| `python3 scripts/data_layer.py query ZN 社库` | 查询单指标 | 即时 |

## 页面接口约定
`/api/indicator?code=XX&id=YY`
- 当前前端是纯静态 GitHub Pages，无后端
- 后续接入图表时，在本机启动一个 Flask/FastAPI 提供该接口
- 接口内部只查本地 SQLite，不碰 Zhiji API

## GitHub 上不能放什么
- `indicators.db` — 二进制，每次重建即可，不推 GitHub
- 环境变量/Key — 通过 `~/.hermes/.env` 读取
- 缓存文件 `~/.hermes/scripts/zhiji_cache/` — 本地临时文件
