# Framework-Tree 交接文档 · 2026-09-08 深夜

> 本轮已完成 **P0 主图串台 + P1 辅助图串台** 两轮整治，全部推送。下一轮从这里继续完善优化。
> 主脑已确认门禁全绿，无未提交改动。**开工前先读 `STATUS.md` 最新两条记录**（P1/P0 详情）。

---

## 1. 当前状态（一切已推送）

| 项 | 值 |
|---|---|
| 分支 | `main @ 1c010ba`（已 push origin/main） |
| 提交链 | `53f473c` 串台根治2 → `c9c55dc` P0收官 → `1c010ba` P1清洗 |
| 指标版本 | **v3.75**（`data/indicators_v1.json`，1294 条，120 条 `_main_metric`） |
| 门禁 | check_html **240/240** ✅ · verify_render **240/240** ✅ · reclaim **11/1**（唯一 FAIL 为历史 merge 提交 `d625cad` 无前缀，非本轮引入，**可忽略**） |
| 主图串台 | **0 处**（P0 收官；sn_4_5 无候选指标保留价格主图，已在 `build_5m_batch.py` L112 标注为已知例外） |
| 辅助图串台 | **4 处，全有跨金属声明**（al_3_2_3 / al_7_1 / cu_5_2 / pb_24_spread_system，均属 AGENTS.md §3.5 允许的合理跨金属辅助参照） |
| 工作区 | 干净 |

## 2. 本轮做了什么（两轮串台整治）

### P0 主图串台（`c9c55dc`）—— 5 处 → 0 处
**根因（第四道防线）**：`build_5m_batch.py` L77 硬编码 `MAIN_METRIC.update({...})` 在 JSON `_main_metric` **之后**执行，**覆盖了 JSON 值**。SN_3.1.5 被硬编码 `sn_313_output`（云南年鉴·年频9点·已陈旧被过滤）顶替 → 兜底取第一个日频指标 = 铝棒加工费。

修正 8 处主图（JSON `_main_metric` + 硬编码块同步）：

| 页面 | 原主图（错） | 新正主 |
|---|---|---|
| al_5_3 | SHFE铝收盘价 | al_53_export 铝材出口量(139点·海关月) |
| sn_3_1_3 | 铝棒加工费 | sn_313_import_tin_ore 锡矿砂进口云南(103点·月) |
| sn_3_1_5 | 铝棒加工费 | sn_71_tc 锡精矿40%Sn加工费(2120点·日) |
| sn_5_3 | SHFE锡收盘价 | sn_53_output_tin_ore 秘鲁明苏尔锡矿产量(45点·季) |
| si_3_1_5 | 硅石价格(陈旧2025-11) | si_315_util_industrial_si 工业硅开工率(106点·周) |
| si_3_2_4 | 硅锰利润(多晶硅板块串台) | si_324_profit 工业硅421#利润新疆(186点·周) |
| si_4_3 | GFEX硅收盘价 | si_43_inv 工业硅工厂库存(65点·周) |
| zn_6_3 | SHFE锌收盘价 | zn_63_coated_export 镀锌板出口量(55点·月) |

连带修复：`build_cu_al_batch.py` L399 `meta["indicators"]` → `meta.get("indicators", meta)` 兼容 flat dict；补拉 2 条无缓存幽灵正主（al_53_export/sn_53_output_tin_ore）；`sn_71_tc` 追加 `_nodes: ["3.1.5"]`。

### P1 辅助图串台（`1c010ba`）—— 18 处 → 4 处（全有声明）
**架构级根因**：`_nodes` 是「节点号」不含品种维度 → 3.1.3 节点池混 40 个跨品种指标。`build_5m_batch.py` 已按品种×节点过滤，但 **`build_cu_al_batch.py` 默认 `comm_only=None` 不分离铜铝** → cu 页混入 al 指标。**修法 = 分两次跑 `--cu-only` / `--al-only`**。

指标层污染 4 条清洗（`_nodes` 清空退出节点池）：
- `sn_313_tc_tc` / `sn_313_tc_tc_2`（铝棒6063加工费无锡）→ 退出锡 3.1.3/3.1.5
- `sn_25_recycle_price`（再生铝棒6063价格）→ 退出锡 2.5/7.3
- `sn_21_premium`（电解铝现货升贴水无锡）→ 退出锡 2.1
- `si_22_price_industrial_si`（SMM A00电解铝现货）→ 退出硅 2.2

根因 = 知几搜索「锡精矿加工费」「锡价」等返回了铝系列序列，注册时按 mid 前缀误归类。

`cu_5_2.html` 补跨金属声明（c3 图用 cu_5_2_consumption_4「SMM电解铝平衡终端消费」作铜消费参照）。

## 3. 下一轮待办（按优先级）

### P0 ⭐ `refresh_cache.py` L82 崩溃（会阻塞下次拉数）
```python
# 现状（崩溃）
i_entries = {k: v for k, v in meta["indicators"].items()...
# 修法（与 build_cu_al_batch.py 一致）
i_entries = {k: v for k, v in meta.get("indicators", meta).items()...
```
`indicators_v1.json` 自 v3.65 起是 **flat dict**（无 `indicators` 顶层键），`refresh_cache.py` 一直崩但未被触发（之前用 zhiji_api.py 直接拉数绕过）。**下次要用统一脚本拉数必撞**。

### P1 `build_cu_al_batch.py` 无跨金属声明自动生成
现在跨金属声明靠**手工 patch HTML**（cu_5_2 已补），**下次全量重建会丢**。应在引擎层加：`build_node` 检测到 `data` 池混入跨品种指标时自动注入声明（格式照 al_3_2_3.html）。

### P2 cu_5_2 note 文案串台
页面 note 写「5.2 定义：**铝**终端细分消费」——cu 页取了铝的 theme 文案。根因 `theme_of()` 按主图品种选文案，但 cu_5_2 主图是铜。查 `THEMES["5.2"]` 是否被铝覆盖。

### P3 sn_4_5 无候选指标
节点池 0 指标，保留 SHFE 锡收盘价当主图（已知例外）。要真正修需同花顺发散补锡隐性/在途库存指标。

### P4 铜铝缺口 10 页（需 Step1 发散全流程）
铜 5 页（4.1/5.2/5.3/6.3/6.4）+ 铝 5 页（3.1.2/3.1.4/6.1/6.4/7.3），`indicators_v1.json` 注册指标数 = 0。**不能直接建页**，必须走「同花顺发散 → 知几验证 → 注册 → 建页」全流程。详见 `STATUS.md` 卡点区 #6。

### P5 页脚版本碎片化（暂缓）
v1.9~v3.75 共 20+ 种版本混存，check_html 对版本校验宽松不阻塞。统一需按品种批量重建 200+ 页，成本高。

## 4. 关键坑（新会话必看，本轮实测踩过）

1. **JSON 改 `_nodes` 必须在同一次执行内写回**：只改内存不 `json.dump` 会让修改丢失（本轮踩了 2 次）。改完必须**立即回读验证** `d2 = json.load(...); print(d2[k]["_nodes"])`。

2. **`build_5m_batch.py` CLI 参数有 bug（未修）**：传节点参数时 L392 `plan=sorted(args)` 变纯字符串 → L437 走 `g.get(node)` 跨品种聚合 → **只建 zn 页且退化回跨品种混入**。**正确用法 = 不传参数全量重建**：`python3 scripts/build_5m_batch.py`

3. **`build_cu_al_batch.py` 必须分两次跑**：`--cu-only` 建铜页、`--al-only` 建铝页。不带参数会铜铝混合污染。

4. **check_html.py 的 PAGES 用 `ast.literal_eval` 解析**（非 json.loads），是**单引号 + `True`/`False`** 的 Python 字面量格式。用 `json.dumps` 写回会产出 `true` 导致 `NameError`。改注册表用 `execute_code` 读 AST → 改 dict → 转 Python 字面量写回。

5. **check_html.py 的 key 命名不统一**：cu 带下划线（`cu_2_1`/`cu_3_1_3`）、sn/zn/si 压缩式（`sn_313`/`zn_63`/`si_315`）、pb 用板块号（`21`/`63`）。同步注册表前先 `print([k for k in P if k.startswith('cu')])` 确认实际 key。

6. **cid 格式**：`echart_{品种码}_{节点号压缩}_c{序号}`，如 `echart_cu_23_c1`（2位）、`echart_sn_313_c1`（3位）、`echart_si_43_c1`（2位）。正则用 `[0-9]+` 别用 `[0-9]{3}`。

7. **重建必改图数 → 门禁必 FAIL**：每次重建页面后必须同步 check_html.py（charts/cids/min_bytes/has_seasonal）+ verify_render.js（charts/seasonal）。用 execute_code 批量解析页面真实数据后回写。

8. **`refresh_cache.py` 不支持五金属前缀**：硬编码 `startswith('i')` 只拉铅 i 指标（STATUS 记录提到兼容 j*，但五金属 cu_/al_/zn_/sn_/si_/li_ 前缀需另行确认）。本轮用 `zhiji_api.py` 直接拉数绕过。

9. **知几缓存 code 是大写**：`load_metric(mid, code)` 的 code 参数是 `CU`/`AL`/`ZN`/`SN`/`SI`/`LI`（大写），不是小写品种码。

10. **pre-commit hook 强制**：改产物文件但没动 `STATUS.md` 会被拦截。逃生通道 `git commit --no-verify`（别滥用）。

11. **数据陈旧阈值 180 天**：`build_node` 的 `is_stale()` 会剔除末点距今 >180 天的序列。al_2_2/al_2_3/al_3_2_3 的图数退化是 `al_22_spot`（陈旧2022）/`al_22_open_spread`（无缓存）/`al_323_import_scrap`（陈旧2019）所致，属真实数据状态。

12. **`--al-only` / `--cu-only` 全量重建有副作用**：数据陈旧的页图数会退化导致 verify_render FAIL。若不想改这些页，重建后 `git checkout -- <退化页>` 恢复到 HEAD（本轮对 al_2_2/2_3/2_4/3_2_3 做过）。

## 5. 关键命令速查

```bash
cd ~/framework-tree
# 重建五金属全部页面（不传参数！传参数有 bug）
python3 scripts/build_5m_batch.py
# 重建铜/铝（必须分两次）
python3 scripts/build_cu_al_batch.py --cu-only
python3 scripts/build_cu_al_batch.py --al-only
# 重建总览
python3 scripts/build_overview_all.py
# 三道门禁
python3 scripts/check_html.py
node scripts/verify_render.js
python3 scripts/reclaim.py
# 拉单指标（绕过 refresh_cache.py 的 bug）
python3 ~/.hermes/scripts/zhiji_api.py series <id> 2015-01-01 2026-09-08
# 写缓存（手动，参考本轮 execute_code）
#   indicator_cache(code,metric,zhiji_id,data_json,fetched_at,error_msg,name,unit,freq)
#   code=大写品种码，data_json={"points":[{"date":...,"value":...}],"name":...,"unit":...,"freq":...}
# 跨品种串台扫描
python3 -c "
import re,os
VAR={'cu':['铜'],'al':['铝'],'pb':['铅'],'zn':['锌'],'ni':['镍'],'sn':['锡'],'li':['锂'],'si':['硅']}
for f in sorted(os.listdir('.')):
    if not re.match(r'^(cu|al|pb|zn|ni|sn|li|si)_\d',f) or not f.endswith('.html'): continue
    var=f.split('_')[0]; h=open(f,encoding='utf-8').read()
    for t in re.findall(r'class=\"chart-title\">([^<]+)<',h):
        t2=re.sub(r'（主图[^）]*）|（补充[^）]*）','',t)
        for ov,ws in VAR.items():
            if ov==var and any(w in t2 for w in ws): print(f,var,ov,t[:60]);break"
# 推送（Pages 限频）
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

## 6. 关键路径

| 文件 | 用途 |
|---|---|
| `data/indicators_v1.json` | 指标元数据唯一真源（flat dict，v3.75，1294 条） |
| `data/tree_config.json` | 目录树配置（8 品种 × 33 节点，含 q 字段定义） |
| `scripts/chart_kits.py` | 图表公共模块（**只有主脑能改**，L106 `load_metric(mid, code)`） |
| `scripts/build_5m_batch.py` | 五金属建页（zn/ni/sn/si/li，L77 硬编码 fallback 覆盖 JSON 注意） |
| `scripts/build_cu_al_batch.py` | 铜铝建页（**必须分 --cu-only/--al-only**） |
| `scripts/check_html.py` | 静态门禁（PAGES 是 Python 字面量，240 页） |
| `scripts/verify_render.js` | 渲染门禁（jsdom，240 页） |
| `scripts/api_cache.db` | SQLite 缓存（code=大写品种码，表 `indicator_cache`） |
| `STATUS.md` | 全局状态唯一真源（先读最新两条） |

## 7. 已改文件清单（勿重复改动）

- `data/indicators_v1.json` — v3.75，含 `_main_metric` 120 条，4 条 `_nodes` 清空
- `scripts/build_5m_batch.py` — 硬编码 fallback 删 SN_3.1.5 条目（改由 JSON 提供）
- `scripts/build_cu_al_batch.py` — flat dict 兼容 + `"5.3":"al_53_export"` 主图
- `scripts/check_html.py` — PAGES 240 页同步（sn_313 4→3、sn_315 3→2、sn_73 4→3、cu_313/315/324/62 →1 等）
- `scripts/verify_render.js` — 21 页同步（含补 cu_315/cu_321 缺失的 charts 字段）
- `cu_5_2.html` — 手工加跨金属声明（**下次重建会丢，见 P1 待办**）
- `STATUS.md` — P0/P1 两条记录已写
