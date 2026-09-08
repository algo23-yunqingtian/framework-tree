# Framework-Tree 交接文档 · 2026-09-08 晚

> 本会话主脑已完成「指标串台根治」两轮修复，全部推送。开新会话前先读本文件 + STATUS.md。

---

## 1. 当前状态（一切已推送，无未提交改动）

| 项 | 状态 |
|---|---|
| 分支 | main @ 53f473c（已 push origin/main） |
| 门禁 | check_html **240/240** ✅ · verify_render **240/240** ✅ · overview 153/153 |
| 指标版本 | v3.72（data/indicators_v1.json，1294 条） |
| 工作区 | 干净（147 文件已提交，勿再动） |

## 2. 本次做了什么（两轮串台根治）

### 根因链（四道防线全失效）
1. **freq 误标**：`infer_freq()` 逻辑 bug → 397 条月/周/季频被标 daily → 引擎兜底 `is_daily()` 全命中 = 随机取第一个当主图
2. **_nodes 万能挂载**：26 条指标挂 4-18 节点（ni_21_close_front 挂 18 节点、zn_22_lme_inv 巴林库存挂 10 节点）
3. **MAIN_METRIC 零覆盖**：ZN/SN/SI/LI 一条都没有 → 兜底取字典序第一个
4. **build 引擎跨品种混入**：`node_indicators()` 按节点聚合所有品种指标，`build_node` 只在 `--zn-only` 等 CLI 参数下过滤 → zn_4_3 混入 ni 库存、zn_2_4 混入镍价格

### 修复动作
| 动作 | 文件 | 量 |
|---|---|---|
| freq 大清洗（按名字括号内频率重算） | data/indicators_v1.json | 397 条（170 daily→monthly 等） |
| _nodes 归一化（价格→2.x，库存→4.x，产量→3.x，进口→6.x） | data/indicators_v1.json | 56 条 |
| MAIN_METRIC 写入 `_main_metric` 字段 + build 引擎动态读取 | data/indicators_v1.json + scripts/build_5m_batch.py | 119 条（ZN30+SN29+SI30+LI30） |
| build 引擎按品种×节点分组过滤 | scripts/build_5m_batch.py | main() plan 改 `(code, node)` 元组 |
| chart_kits.py flat dict 兼容 | scripts/chart_kits.py | `meta.get("indicators", meta)` |
| 门禁注册表批量同步 | scripts/check_html.py + scripts/verify_render.js | check_html 73 条 + verify 36 条 |
| overview 重建 | scripts/build_overview_all.py | 31 页 153/153 |

### 效果
- 主图串台：**33 → 5 处**（剩余为缺贴题指标的价格兜底）
- 辅助图串台：**60 → 21 处**（剩余为 cu/sn 间铝指标残留 + 合理交叉验证）
- 用户点名问题全部消除：zn_4_1 主图=LME锌库存、zn_4_2=SHFE仓单、zn_3_2_3=原生锌产量（精炼锌进口已移至 6.x）、zn_5_3=PMI

## 3. 剩余工作（新会话从这里继续）

### P0 剩余 5 处主图串台（需发散补贴题指标）
| 页面 | 当前主图（错） | 需要 |
|---|---|---|
| al_5_3 | SHFE铝收盘价 | 铝消费先行指标（如铝材开工率/PMI相关） |
| sn_3_1_3 / sn_3_1_5 | 铝棒加工费 | 锡精矿 TC/加工费 |
| sn_4_5 / sn_5_3 | SHFE锡收盘价 | 锡库存/消费先行 |
| si_3_1_5 / si_3_2_4 / si_4_3 | GFEX工业硅收盘价 | 硅 TC/利润/库存 |
| zn_6_3 | SHFE锌收盘价 | 锌制品出口（已有指标但被价格抢了正主？查 MAIN_METRIC ZN_6.3） |

### P1 辅助图 21 处串台
- cu_3_1_5 / cu_3_2_4 混入铝棒加工费、氧化铝成本 → 清洗 `cu_313_tc_tc*` 的 _nodes
- sn_3_1_3 / sn_3_1_5 混入铝棒加工费 → 清洗 `sn_313_tc_tc*`
- al_3_2_3 混入再生铜杆产量 → 清洗 `al_323_*` 或改用铝再生指标
- ni_3_2_4 有云南罗平锌电利润（跨品种锌）→ 清洗 `ni_25_profit_2/3` 的 _nodes

### P2 页脚版本碎片化
- v1.9~v3.72 共 23 种版本混存，check_html 对版本校验宽松不阻塞
- 需统一需按品种批量重建 200+ 页，成本高，暂缓

## 4. 关键命令速查

```bash
cd ~/framework-tree
# 重建五金属全部页面
python3 scripts/build_5m_batch.py
# 重建单品种（跨品种混入已自动过滤，无需 --zn-only 等参数）
python3 scripts/build_5m_batch.py 4.3          # 按节点
# 门禁三道
python3 scripts/check_html.py
node scripts/verify_render.js
python3 scripts/reclaim.py
# 重建总览
python3 scripts/build_overview_all.py
# 推送（Pages 有限频）
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

## 5. 已改文件清单（勿重复改动）

- `data/indicators_v1.json` — v3.72，含 `_main_metric` 字段（119 条）
- `scripts/build_5m_batch.py` — 品种×节点分组 + MAIN_METRIC 动态读取 + flat dict 兼容
- `scripts/chart_kits.py` — flat dict 兼容
- `scripts/check_html.py` — PAGES 全量同步（注意：现为 JSON 双引号格式，改时用 execute_code 改 dict 再 dump，别手写）
- `scripts/verify_render.js` — 注册表同步（36 条）
- `STATUS.md` — 已记录两轮修复详情

## 6. 重要坑（新会话必看）

1. **check_html.py 的 PAGES 现在是 json.dumps 格式（双引号）**，别用单引号 patch；用 execute_code 读 AST → 改 dict → json.dumps 写回
2. **build_5m_batch.py 的 plan 是 `(code, node)` 元组**，不是纯节点字符串；CLI 参数 `4.3` 仍是节点过滤，但页面文件名按品种自动推断
3. **MAIN_METRIC 在 JSON 的 `_main_metric` 字段**（key = "ZN_4.1"），引擎启动时读取；硬编码 fallback 在 build 脚本第 76 行附近（CU/AL/PB）
4. **freq 字段现在可信**（刚清洗过 397 条），但新注册指标仍要走 `infer_freq` 修复版逻辑——若知几返回名字含"（月）（周）（季）（年）"却没带 freq，注册时手动补
5. **reclaim.py 唯一 FAIL**：历史 merge 提交 d625cad 无前缀，非本次引入，可忽略
6. **zn_3_1_3 主图是"锌精矿进口加工费均价"**（原设计矿产量），若用户要求改回产量需发散补 `zn_313_output*` 指标
