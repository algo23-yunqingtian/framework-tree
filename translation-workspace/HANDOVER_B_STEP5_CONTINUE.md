# HANDOVER — 指标翻译线 Agent B 三品种（LI/SI/SN）建页交接

> 生成：2026-09-01 · 用途：上下文压缩/换会话后的续接入口
> 当前工作分支：`translation-workflow`（远端最新 `7d9f8fc`）
> 浏览器预览（GitHub Pages）：`https://algo23-yunqingtian.github.io/framework-tree/`

---

## 一、当前完成状态

### 已完成的（Agent A 承接，已推送）
| 步骤 | 状态 | 产物 |
|---|---|---|
| ZN/CU/AL/NI Step1 审计 | ✅ 23/24（CU_进出口卡点，AI拒答待人工） | `translation-workspace/audit/{ZN,CU,AL,NI}/audit_*.md` |
| ZN/CU/AL/NI Step2 知几验证 | ✅ 833 条 | `translation-workspace/mapping/{ZN,CU,AL,NI}/step2_match_*.json` |
| ZN/CU/AL/NI Step5 建页 | ✅ 20 页 427 图（已推送） | 根目录 `zn_*.html` 等 + `scripts/build_translation.py` + `scripts/step2_cache_load.py` |

### 刚完成的（CSV 归档入库）
| 品种 | CSV 原文落盘 | 标准 JSON |
|---|---|---|
| LI（碳酸锂） | `translation-workspace/mapping/raw/B_LI.csv`（95行） | `translation-workspace/mapping/LI/step2_match_LI.json`（95条，A79/B10/C6）|
| SI（工业硅） | `translation-workspace/mapping/raw/B_SI.csv`（145行） | `translation-workspace/mapping/SI/step2_match_SI.json`（145条，A135/B7/C3）|
| SN（锡） | `translation-workspace/mapping/raw/B_SN.csv`（152行） | `translation-workspace/mapping/SN/step2_match_SN.json`（152条，A119/B20/C12）|

### 转换方式
`csv_to_match_json.py --csv translation-workspace/mapping/raw/B_{品种}.csv`
- name ← 图名称（用户默认口径）
- hit_id ← 知几ID / hit_name ← 知几名称 / grade ← 置信度 / subnode ← 子节点
- ⚠️ 字段 name 取"图名称"是用户确认前的默认，如需"同花顺概念名"用 `--name-field 同花顺概念名` 重转

---

## 二、⚠️ 已知质量问题（建页前必须处理）

### 1. B 的置信度不可全信（语义污染）
B 的 A 级里有大量**知几名称与品种/指标语义对不上**的条目：
- LI 2.2 "氢氧化锂现货升贴水" → `a10099482 SMM: 精炼锡进出口盈亏`（标A，错）
- LI 2.3 "LME锂价" → `s22862195 SMM: 溴化锂-最高价`（标A，错）
- SN 5.3 "锡化工订单量" → `a10170529 GFEX: 工业硅仓单日报`（标A，错）
- SN 4.4 "国内工厂库存总量" → `a12715352 SMM: 无锡铝锭日度库存量`（标A，错）
- SI 3.1.3 "国内硅矿产量" → `ID02467748 日本水泥协会矿渣硅酸盐水泥销量占比`（标A，错）

**处理决策（用户前一指令）：建页时 A 级为主图，B/C 作辅助或剔除。但在灌库+建页前必须加一道"知几名称语义校验"**：hit_name 不含品种词（锂/碳酸锂/氢氧化锂/工业硅/锡）的，降级到 B 或剔除。这一步 A 侧 ZN/CU/AL/NI 在 Step2 曾用"品种词命中"逻辑，可直接复用思路。

### 2. 板块列全空
B 的 CSV"板块"列全部为空，只有子节点号（2.1/3.1.1…）。
现有 `build_translation.py` 用 subnode 首数字自动归板块（2→价格/3→供给/4→库存/5→需求/6→进出口/7→成本利润），所以**不用补板块列**，引擎自动归位。

### 3. 子节点键重复
部分条目 key 用 `subnode|name`，同一子节点下 name 重复会覆盖（如 SN 4.1 多个"沪锡仓单注册量"）。已按"后写覆盖"处理，不影响主流程（重复的多是别名图）。

---

## 三、下一步待做（建页三连）

```bash
cd /home/ubuntu/framework-tree
# 1) A级语义校验 + 数据可得性实测（过滤无序列/错配）
/tmp/audit_env/bin/python -u - <<'EOF' > /tmp/series_check_BSI.log 2>&1
# 对 LI/SI/SN 的 A 级 hit_id 逐个拉 series 确认有数据，输出 [无数据] 行
EOF

# 2) 灌库（把有数据的 hit_id 写入 api_cache.db）
/tmp/audit_env/bin/python scripts/step2_cache_load.py --all --only-verified

# 3) 建页（需要先给 build_translation.py 扩展 CODE_CN/CODE_COLOR 加 SN/SI/LI）
/tmp/audit_env/bin/python scripts/build_translation.py --all

# 4) 校验 + 提交
python3 scripts/check_html.py 2>&1 | tail -5
git add . && git commit -m "[A-STEP5b] 翻译线 AgentB 三品种(LI/SI/SN)建页" && git push
```

**引擎改动点**（scripts/build_translation.py）：
- `CODE_CN` 加 `"SN": "锡", "SI": "硅", "LI": "锂"`
- `CODE_COLOR` 加对应色
- SECTION_NAME 已覆盖 2-7 板块（价格/供给/库存/需求/进出口/成本利润）

---

## 四、关键文件索引
| 文件 | 说明 |
|---|---|
| `scripts/build_translation.py` | 建页引擎（读 mapping/step2_match_*.json，板块级出页）|
| `scripts/step2_cache_load.py` | 灌库（hit_id→api_cache.db）|
| `scripts/csv_to_match_json.py` | CSV→标准 JSON 转换器（已用于 B 三品种）|
| `scripts/xml_to_match_json.py` | XML→JSON（备用，B 实际是 CSV）|
| `translation-workspace/HANDOVER_AGENT_B_STEP5.md` | 给 B 的建页提示词（早期版本，已过期需更新）|
| `translation-workspace/mapping/raw/B_{LI,SI,SN}.csv` | B 原始 CSV 归档 |
| `STATUS.md`「近期变更记录」 | 唯一真源 |

## 五、用户偏好提醒
- 改产物文件必须同步 STATUS.md，否则 pre-commit 拦
- B 在 Windows 无 git，所有落盘/建页/推送由 A 完成
- 页面预览走 GitHub Pages：`https://algo23-yunqingtian.github.io/framework-tree/`
- 每一步执行后 ≤800 字汇报 + `MEDIA:` 可分享路径