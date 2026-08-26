# 交接文档 · 有色金属产业指标树

> 更新：2026-08-26 20:00  
> 版本：v1（目录树上线 + 实时API + 3天滑动缓存）

## 当前状态
- ✅ GitHub Pages 上线：`algo23-yunqingtian.github.io/framework-tree/`
- ✅ 目录树完全复刻 amiya 形态（7大类×33指标×258品种chip）
- ✅ 数据层 v1：**实时调 Zhiji + 3天滑动缓存**
  - 本地启动 `api_server.py`，点 chip 才加载
  - 3天内重复访问读缓存，不消耗 API
  - 超过3天自动失效重新拉
- ✅ 前端适配双模式（本地=实时数据，GitHub Pages=静态提示）
- ✅ 文档同步推 GitHub

## 待做
- [ ] **验证指标 ID**——当前 `api_server.py` 和 `data_layer.py` 中的 Zhiji ID 大部分是占位，需 `search→series` 逐一验证
- [ ] 接入完整 ECharts 四图（时序/季节性/价格叠加/关键数据）
- [ ] 铜/铝/铅/锡/锂/硅 6 品种同花顺对话
- [ ] 注册 supervisor 常驻 `api_server.py`

## 本地关键路径
| 路径 | 用途 |
|---|---|
| `/home/ubuntu/framework-tree/` | 项目根目录（GitHub同步） |
| `/home/ubuntu/framework-tree/scripts/api_server.py` | **核心**：Flask API + 3天滑动缓存 |
| `/home/ubuntu/framework-tree/scripts/data_layer.py` | 备用：全量SQLite方案 |
| `/home/ubuntu/framework-tree/index.html` | 前端（配置已内联） |
| `/home/ubuntu/framework-tree/docs/architecture.md` | 架构设计 |
| `/home/ubuntu/analysis/handover_indicatortree_20260826.md` | 原始交接文档 |
| `/home/ubuntu/.hermes/scripts/zhiji_api.py` | Zhiji客户端 |

## 启动命令
```bash
python3 /home/ubuntu/framework-tree/scripts/api_server.py 8786
# 然后浏览器访问 http://127.0.0.1:8786
```

## 技术要点
1. Zhiji 无额度，只有 1秒限频
2. Git push 用 `GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10"`
3. GitHub Pages 是静态的，无后端 → 图表必须本地看
4. 数据 ID 是占位符，接入图表前必须验证

## 给后续 Agent
1. 先读 `docs/architecture.md` 了解数据流
2. 启动 `api_server.py` 测试 `/api/indicator?code=ZN&metric=LME库存`
3. 验证返回真实数据后，再逐指标验证 ID
4. 接入 ECharts 替换当前数据卡面板
