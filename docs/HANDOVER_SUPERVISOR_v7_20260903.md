# HANDOVER SUPERVISOR v7（2026-09-03）— 极简版

> 目标：新对话直接开工，不读旧会话。只留「现在在哪 + 下一步做什么 + 怎么动手」。

## 1. 现在在哪（已 push main @ be00158，工作区干净）

- **指标库**：`data/indicators_v1.json` → **v3.62，1290 指标**（上次交接 v3.54/1070 → +220）
- **门禁基线**：check_html 234/234 ✅ · verify_render 238/238 ✅ · reclaim 12/0 ✅
- **页面**：274 节点页 + 总览页；全品种 1-7 板块节点页已无缺口
- **缓存**：`scripts/api_cache.db`（不推 GitHub）；PB/SI/SN/CU/AL 已全刷

## 2. 已完成（本会话 12 commits，无需重做）

| 批次 | 内容 | 结果 |
|---|---|---|
| P3-CU/ZN/NI/SN/AL/PB/LI·SI | correction 全 8 品种解析补注册 | 155 指标，含假命中排除 18+ |
| P4-GAPS | CU 5.2/5.3/6.3/6.4 + AL 3.1.2/3.1.4/6.1/6.4/7.3 **9 缺口页首次可建** | 63 指标，知几 API 发散替代同花顺 |
| P4-EXTRA | LI 7.3(3图) + SI 3.1.3(2图) + SI 5.3(2图) 首次可建 | 3 页 |
| 基建 | PAGE_MAP 审计+补 9 映射、verify_render key 格式修正 | — |
| 修复 | build version 双 v bug、cu_6_1 断更剔除降 1 图、indicators indent=1 | — |

## 3. 下一步（按优先级，新对话从这里开始）

### ① SN 3.2.4（冶炼利润，0 指标）+ SI 7.3（能源成本，0 指标）— 发散建页
- 流程（已验证可用，替代同花顺）：知几 search` → series 实测 → 概念级去重 → 注册 → `refresh_cache --code SN/SI` → build
- 工具：`python3 ~/.hermes/scripts/zhiji_api.py search "锡 冶炼 利润"`（**返回字段是 `results`，不是 `data`**，别踩坑）
- 已知问题：SN 3.2.4 / SI 7.3 首轮搜索命中多为年频/不相关（黑色金属/光伏电价），需换词：试 "锡 冶炼 加工费" / "锡 焊料 利润" / "工业硅 电价 电力成本"

### ② 8.x 节点（年度锚 8.1 / 自建平衡表 8.2 / 表观消费拟合 8.3）— 全品种 0 指标
- tree_config 有定义、无页面；**知几搜不到这些**（需人工计算/行业协会数据）→ 属 P5 手工范畴，可先只建 8.1 年度锚（搜得到啥放啥）

### ③ 五金属总览页（ni_2.html/zn_3.html 等板块页为孤儿页，无引用）
- 优先级低；页面已存在，只是 index.html 无入口（五金属走动态推导，可忽略）

## 4. 开工前必做（强制）

```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
git config core.hooksPath scripts/hooks   # pre-commit 强制
bash scripts/bootstrap_agent.sh           # 6 项上线自检（基线/hook/指标/门禁/死链/数据源）
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标:', len(d['indicators']))"  # 必须 ≥1290
```

## 5. 常用命令

```bash
# 知几（key 在 ~/.hermes/scripts/zhiji_api.py，不进仓库）
python3 ~/.hermes/scripts/zhiji_api.py search "锌 社会库存"          # 命中：score≥12=A / 6-11=B
python3 ~/.hermes/scripts/zhiji_api.py series a10193708 2015-01-01 2026-09-01
# 拉缓存（1 秒限频，写 api_cache.db；默认只刷 PB，需 --code 指定）
python3 scripts/refresh_cache.py --code CU   # CU/AL/SN/SI/LI/ZN/PB 均支持
# 建页
python3 scripts/build_5m_batch.py 2.6 --si-only       # 五金属（ZN/NI/SN/SI/LI）
python3 scripts/build_cu_al_batch.py 5.2 --cu-only    # 铜铝
for f in scripts/build_pb_*.py; do python3 "$f"; done # 铅
# 门禁三连（提交前必须全绿）
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py
# push（Pages 有限频，用这串）
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

## 6. 坑速查（犯过的错，别重犯）

1. **知几 search 返回 `results` 字段**（不是 data）——解析错会得到 0 命中
2. **`_nodes` 必须是点号格式 `"5.2"`**（注册时误写成 `"5_2"` 会导致 build 找不到指标 → 全部跳过）
3. **indicators_v1.json 必须 indent=1 写回**（否则 diff 15442 行）
4. **注册前先备份**：`cp data/indicators_v1.json data/backups/indicators_v1_before_<task>_$(date +%Y%m%d_%H%M%S).json`
5. **verify_render key 带品种前缀下划线**：`key: 'cu_52'` 不是 `'cu52'`（DOM 检查按 `echart_cu_52_c1` 取名）
6. **门禁注册表两处都要同步**：`scripts/check_html.py`（PAGES 字典）+ `scripts/verify_render.js`（PAGES 数组）
7. **annual 数据 n<20 排除**（年鉴/USGS 产量多为年频，建页会降级）
8. **断更剔除**：末点距今 >180 天的序列 build 会自动剔除（页面右下 footer 会写明）

## 7. 关键文件

| 文件 | 用途 |
|---|---|
| `data/indicators_v1.json` | 指标元数据唯一真源（1290 条） |
| `data/tree_config.json` | 目录树配置（节点 code/id/q 定义） |
| `STATUS.md` | 唯一真源进度（每次改动必写变更记录） |
| `scripts/build_5m_batch.py` / `build_cu_al_batch.py` | 建页脚本 |
| `scripts/check_html.py` + `verify_render.js` | 门禁注册表（新页必须加条目） |
| `docs/COLLABORATION_PLAYBOOK.md` | 全流程 11 章（格式契约/坑速查） |
| `translation-workspace/correction/` | 各品种 correction（P3 已全量处理完） |