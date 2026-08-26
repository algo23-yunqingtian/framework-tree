# 数据架构设计 · framework-tree v1

## 一句话
**实时调用 Zhiji API + 3天滑动本地缓存**。用户点 chip 才加载该指标，3天内重复访问直接读缓存不消耗 API。

## 数据流
```
用户点 [品种 chip]
  → 前端 fetch http://127.0.0.1:8786/api/indicator?code=XX&metric=YY
    → api_server.py 查本地缓存
      → 3天内有缓存？  是 → 返缓存（重置计时）
                       否 → 调 Zhiji API → 存缓存 → 返回
      → 前端渲染迷你数据卡（最新值/周月年变化）
```

## 双模式部署

| 模式 | 地址 | 行为 |
|---|---|---|
| **本地**（推荐） | `http://127.0.0.1:8786` | 启动 api_server.py，点 chip 实时调 Zhiji + 3天缓存 |
| **GitHub Pages** | `algo23-yunqingtian.github.io/framework-tree` | 静态版，点 chip 显示"需本地启动"提示 |

## 为什么这个方案省
1. **按需加载**——没人看的指标永远不消耗 API
2. **3天滑动缓存**——同一指标 3 天内重复点不重新拉
3. **1秒限频**——Zhiji 每次调用间隔 1 秒，20 个指标 = 20 秒
4. **不是额度**——Zhiji 无月度限制，只有速度限制

## 启动方式
```bash
cd /home/ubuntu/framework-tree
python3 scripts/api_server.py 8786
```

## 接口
| 接口 | 参数 | 返回 |
|---|---|---|
| `GET /api/indicator` | code=ZN, metric=社库 | `{points:[{date,value},...], source:"api"\|"cache"}` |
| `GET /api/cache/stats` | — | `{total, valid_cache, db_size_mb}` |

## 缓存文件
- `scripts/api_cache.db`（SQLite，本地，不推 GitHub）
- 每个 (code, metric) 存一条，含 data_json + fetched_at
- 3 天未访问自动失效（下次访问重新拉）

## 成本核算
| 项目 | 数值 |
|---|---|
| 首次访问某指标 | 1 次 API 调用 + 1-3 秒等待 |
| 3 天内重复访问 | 0 次 API 调用，毫秒级 |
| 每天 cron | 不需要（按需加载） |
| 本地存储 | 每个指标 ~10KB，100 个指标 = 1MB |
