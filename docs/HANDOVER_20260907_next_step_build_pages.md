# HANDOVER 2026-09-07 — 白名单管线已收尾，下一步=统一指标建页

> 新对话读此文件即可直接开工。仓库：`/home/ubuntu/framework-tree`（main @ df6d8ae，已全部 push）

---

## 一、现状一句话

**白名单约束推荐管线已完成**（47/47产物合格、白名单外引用ID=0），两 agent 产物已 merge 成统一指标表（1495条）。**下一步主线：用统一指标表建页（NI/SN/SI/LI 待建页）+ 多指标季节切换函数。**

## 二、已完成（本轮会话产出，均已 push）

| 项 | 结果 |
|---|---|
| 白名单审计脚本化 | `scripts/whitelist_audit.py`，name+ID双匹配，47/47全合格，白名单外引用ID=0 |
| 规则8.1 | 驱动脚本 prompt 强制同花顺回显「指标名（知几ID）」，覆盖率 55.1%→69.4% |
| merge v4分支 | 8品种2667条 v4 重判产物入库（假A=0、复用>3=0） |
| 统一指标表 | `scripts/unify_indicators.py` → `analysis/unified_indicators.json`（1495条，642KB） |
| 频率标准化 | 中英文混杂→英文标准（daily/monthly/weekly/quarterly/yearly/unknown） |

## 三、待办（P0 优先）

### P0-1 五金属建页（NI/SN/SI/LI 当前 0 页）
- 数据源：`analysis/unified_indicators.json`（1495条，A/B级指标可直接用）+ `analysis/iwencai_whitelist/*.md`（47份，含同花顺给的图表设计方案：图名/包含指标/形态/观测用途）
- 参考模板：`scripts/build_5m_batch.py`（ZN 29页的批量建页脚本，工作区已有修改版）
- 建议顺序：NI（覆盖率82.5%最高）→ LI → SN → SI
- 验证：`python3 scripts/check_html.py` + `node scripts/verify_render.js` + `python3 scripts/reclaim.py` 三连全绿

### P0-2 多指标季节切换函数
- 现状：`scripts/chart_kits.py` 的 `chart_line_t` **已实现单指标时序⇄季节切换**（日度→365天MM-DD对齐、月度→12月历年叠加）
- 缺：`chart_dual`（双指标复合图）和 `chart_triple` 没有季节切换
- 任务：扩展 `chart_dual_t`（双指标时序⇄季节），复用现有 `__seasonalizeByYear`/`__seasonalizeByDay`/`__tgl` JS
- 注：`chart_kits.py` 是公共模块，**只有主脑能改**（本项目内主脑=你）

### P1-1 补 527 条 freq=unknown
- 现状：`unified_indicators.json` 里 527 条频率缺失（CU 41%、NI 34%、SN 34% 最严重）
- 方法：用 `~/.hermes/scripts/zhiji_api.py series <id>` 拉数据实测频率，回填
- 影响：不做也能建页，但季节图判断不准

### P1-2 重试 3 个同花顺拒答任务
- `ZN_demand` / `SI_trade` / `LI_price`——同花顺拒答/超时（需求/价格板块可能触发风控）
- 方法：换 prompt 措辞（"分条列举已知数据"类规避表述），命令：
```bash
cd /home/ubuntu/framework-tree
/tmp/iwc_env/bin/python scripts/whitelist_batch_driver.py --variety ZN --board demand
# 需先从 analysis/iwencai_whitelist/_whitelist_state.json 的 done 移除该任务
```

### P2 增量更新白名单
- 新品种/新指标加入后：重新跑 `scripts/unify_indicators.py` 重新合并

## 四、关键文件

| 文件 | 用途 |
|---|---|
| `analysis/unified_indicators.json` | **统一指标表（建页数据源，1495条）** |
| `analysis/iwencai_whitelist/*.md` | 47份白名单产物（含图表设计方案） |
| `analysis/knowledge_base.json` | 白名单知识库（1240条） |
| `analysis/zhiji_match_v4/*.json` | 另一agent的v4匹配产物（2667条） |
| `scripts/unify_indicators.py` | 两源合并脚本 |
| `scripts/whitelist_audit.py` | 产物质量审计 |
| `scripts/whitelist_batch_driver.py` | CDP批量驱动（含规则8.1） |
| `scripts/chart_kits.py` | 图表公共模块（chart_line_t 已含季节切换） |
| `scripts/build_5m_batch.py` | 五金属批量建页模板（工作区有改） |
| `docs/HANDOVER_20260907_whitelist_pipeline.md` | 白名单管线完整脉络 |

## 五、开工前必做（AGENTS.md 强制）

```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
bash scripts/bootstrap_agent.sh    # 6项自检全绿才开工
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"  # 须≥786
```

## 六、⚠️ 工作区注意

- **勿动**：`ni_*.html` / `sn_*.html` / `zn_*.html` / `build_5m_batch.py` 等未提交修改 = 另一 agent 的活
- **勿动**：`analysis/iwencai/prompts/*.md`（另一 agent 的板块8 prompt）
- 改动产物文件必须同步更新 `STATUS.md`（pre-commit hook 会拦截）
- 门禁三连：`check_html.py` + `verify_render.js` + `reclaim.py` 全 PASS 才算完成
- commit 前缀：`[A]`代码 / `[Txx]`任务 / `[B]`数据 / `[DOC]`文档

## 七、环境备忘

- 知几API：`python3 ~/.hermes/scripts/zhiji_api.py search "关键词"`（配额已恢复）
- CDP批量环境：`/tmp/iwc_env/bin/python`（websocket-client 已装）
- Chrome CDP：需 `--remote-debugging-port=9222`
