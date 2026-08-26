# 交接文档 · 线A：framework-tree 架构 + GitHub + 前端

> 更新：2026-08-26
> 版本：v2（新增：两条线隔离 + 协作机制）
> 负责：前端页面、目录树 UI、API 服务器、ECharts 图表、GitHub 部署

---

## 一、当前状态

- ✅ GitHub Pages 上线：`algo23-yunqingtian.github.io/framework-tree/`
- ✅ 目录树复刻 amiya 形态（7大类×33指标×258 chip）
- ✅ 数据 API 骨架：`api_server.py` 实时调 Zhiji + 3天滑动缓存
- ✅ 协作机制文档：`COLLABORATION.md` + `STATUS.md`
- ❌ `api_server.py` 中 Zhiji ID 大部分是**占位符**，待线B验证后替换
- ❌ ECharts 四图（时序/季节性/价格叠加/关键数据）尚未接入

---

## 二、线A写权限范围

**允许写**：
- `/home/ubuntu/framework-tree/`（全部）

**禁止写**（属线B）：
- `/home/ubuntu/analysis/iwencai/`
- `/home/ubuntu/analysis/spec/`
- `/home/ubuntu/analysis/temp/`

> 文件锁白名单已配置（`~/.hermes/scripts/file_write_lock.py`），违规写入会被拒。

---

## 三、协作规则（读 STATUS.md 再开工）

| 规则 | 说明 |
|---|---|
| 开工前 | 先读 `framework-tree/STATUS.md`，看是否有 B→A 待办 |
| 接手线B数据 | 看 STATUS.md "B→A 待办"区 → 接指标进 api_server.py → 更新 STATUS.md → git push |
| 推 GitHub | 每次修改 STATUS.md 后 30 秒内 commit + push |
| commit 前缀 | `[A]` (代码) / `[DOC]` (文档) |

---

## 四、待做（按优先级）

| # | 任务 | 依赖 |
|---|---|---|
| 1 | 注册 supervisor 常驻 `api_server.py` | 无 |
| 2 | 等线B首个品种(铅库存)数据就绪 → 接 zhiji_id + ECharts 四图 | 线B完成铅库存 |
| 3 | 模板化 ECharts 图表组件（后续品种复用） | 铅库存接入验证 |
| 4 | 其余品种陆续接入 | 线B逐个交付 |

---

## 五、关键路径

| 路径 | 用途 |
|---|---|
| `/home/ubuntu/framework-tree/` | 项目根目录 |
| `scripts/api_server.py` | **核心**：Flask API + 3天滑动缓存 |
| `data/tree_config.json` | 目录树配置（前端内联副本在 index.html） |
| `STATUS.md` | 全局状态同步（与线B共用） |
| `COLLABORATION.md` | 协作机制 |

---

## 六、启动 & Git

```bash
# 启动 API
python3 /home/ubuntu/framework-tree/scripts/api_server.py 8786

# Git push
cd /home/ubuntu/framework-tree
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

---

## 七、新对话第一句话

> 读取 `/home/ubuntu/framework-tree/STATUS.md`，确认有无 B→A 待办；然后读取 `docs/handover_a.md`，继续 framework-tree 线A工作。