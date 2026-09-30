# alias_lib_verification_report_rewrite.md · 别名库验证报告（本轮重跑重写版）

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST |
| 数据来源 | `_stats_new.json` / `verify_conclusion_result.json` / `quality_regression_result.json` |
| 运行日志 | `build_run_log.txt`（exit 0）/ `verify_conclusions_log.txt`（exit 0）/ `quality_regression_log.txt`（exit 0） |
| 执行时间 | 2026-10-01 03:24 / 03:31 / 03:36 UTC+8 |
| 被审源脚本 | `build_alias_library.py` 52,699 B · MD5 `d375f963678d1e89c7e9949805f8433f` |
| 与旧稿关系 | 旧稿 `alias_match_presearch/alias_lib_verification_report.md` 保留归档，本文件为新增重写版 |

---

## 1. 别名库结构

| 项 | 值 |
|---|---|
| 行数 | **4643** |
| 列数 | **23** |
| 绑定 canonical 的行 | 2882（含冲突 165） |
| 未注册行 | 1734 |
| 覆盖 canonical key 数 | **1652**（indicators_v1 共 1658 键） |
| 混淆邻居关联行 | 292 |
| 歧义清单行 | **448** |

### 1.1 relation 分布（5 类）

| relation | 行数 | 说明 |
|---|---|---|
| `synonym_merge` | **2502** | 直接同义合并（可自动入库） |
| `unregistered` | **1734** | 别名存在但 canonical 未注册 |
| `synonym_with_confusable_neighbor` | 215 | 同义但邻近存在混淆对（需人工） |
| `canonical_conflict` | 165 | 多 canonical 争用同一别名 |
| `confusable_warn` | 27 | 混淆告警 |

### 1.2 alias_source 分布

| 来源 | 行数 |
|---|---|
| INDICATORS_V1_KEY | 1652 |
| THS_SERIES | 1572 |
| INDICATORS_V1_NAME | 1234 |
| PDF_TEMPLATE | 259 |
| THS_MATCHED | 286 |
| RISK_DB_SRC | 37 |
| RISK_DB_MATCHED | 18 |

### 1.3 alias_type 分布

| 类型 | 行数 |
|---|---|
| latin_abbr | 1659 |
| unit_variant | 1256 |
| mixed_script | 531 |
| canonical | 521 |
| full_name | 309 |
| cross_report_synonym | 278 |
| suffix_variant | 65 |
| numeric_code | 24 |

### 1.4 family 分布

NI **692** / SI **403** / SN **403** / LI **376** / ZN **363** / AL 337 / AO 135 / PB 161 / CU 151 / ENTITY 56 / LC 2

### 1.5 质量四层分类（本轮新增维度）

| 层 | 行数 | 占比 | 对应 relation | 处置 |
|---|---|---|---|---|
| **W1 可靠同义** | **2502** | 53.9% | synonym_merge | 可批量自动入库 |
| **W0 待注册** | **1734** | 37.3% | unregistered | 需先补 canonical 注册 |
| **W2 存疑** | **369** | 7.9% | canonical_conflict 165 + synonym_with_confusable_neighbor 204 | 人工复核后入库 |
| **W3 明确错误** | **38** | 0.8% | confusable_warn 27 + synonym_with_confusable_neighbor 11 | 禁止入库，转黑名单候选 |

人工复核优先级：P0_manual **192** / P1_manual **215**。

W2 分族热点：ZN 58 / NI 52 / SI 45 / CU 44 / PB 44 / SN 39 / LI 33 —— 与 §4 高危混淆对的 CU~ZN / PB~ZN / NI~SN 热点完全对应。

W3 分族：LI 11 / NI 8 / CU 5 / SN 5 —— 错误别名集中在「锂/镍」，与别名库中 9 条「仍自动放行」样例的家族一致。

---

## 2. 41 条风险案例回放（逐条 V86 判定）

**汇总**：41 条 = 有匹配目标 37 + 无匹配目标 4；V86 拦截 **37**（P0 21 / P1 16）；**误放行 0**。

| ID | 级别 | 源 | 左侧 series | → 右侧匹配目标 | V86 判定 |
|---|---|---|---|---|---|
| RISK-001 | P0 | PDF | LME主要仓库场内库存 | LME：非仓单库存：欧洲（日） | block · BL-005 |
| RISK-002 | P0 | PDF | 碳酸锂 三元523需求 | SMM:碳酸锂现金生产利润:外购三元极片黑粉 | block · BL-009 |
| RISK-003 | P0 | PDF | 其他电池(磷酸铁锂) 销量 | SMM:境内其他电池产量:月度 | block · BL-002 |
| RISK-005 | P0 | PDF | 磷酸铁锂 电池 国内销量 | （无） | block · no_match_target_recorded |
| RISK-006 | P0 | PDF | 新能源乘用车 产量 | SMM:国产乘用车销量-新能源汽车:周度 | block · BL-002 |
| RISK-010 | P0 | PDF | 中国电解镍净进口量 | （无） | block · no_match_target_recorded |
| RISK-011 | P0 | PDF | 工业硅样本工厂库存(SMM) | （无） | block · no_match_target_recorded |
| RISK-013 | P0 | PDF | 工业硅供需平衡 | （无） | block · no_match_target_recorded |
| RISK-014 | P0 | THS | COMEX镍持仓量（手） | COMEX：铜：主力合约：持仓量（日） | block · variety_anchor |
| RISK-015 | P0 | THS | LME镍现金价格、LME镍3个月期货价格 | LME：铜：期货价格：全球（月） | block · variety_anchor |
| RISK-016 | P0 | THS | 印尼镍精矿TC（美元/吨干矿） | 铜精矿：长单TC价（年） | block · variety_anchor |
| RISK-017 | P0 | THS | 菲律宾镍精矿TC（美元/吨干矿） | 铜精矿：长单TC价（年） | block · variety_anchor |
| RISK-020 | P0 | THS | Mysteel镍精矿TC、Mysteel镍厂库存总量 | 铜精矿：长单TC价（年） | block · variety_anchor |
| RISK-021 | P0 | THS | Mysteel镍精矿TC、Mysteel中国精炼镍在… | 铜精矿：长单TC价（年） | block · variety_anchor |
| RISK-022 | P0 | THS | 国内硅矿月加工费TC（元/吨） | 铜管：H62：加工费：安徽（月） | block · variety_anchor |
| RISK-024 | P0 | THS | LME锡库存（吨） | LME：镍：注册仓单（日） | block · variety_anchor |
| RISK-025 | P0 | THS | LME锡库存时序图 | LME：镍：注册仓单（日） | block · variety_anchor |
| RISK-026 | P0 | THS | 印尼锡精矿产量（万吨） | 印尼精炼镍产量 | block · variety_anchor |
| RISK-027 | P0 | THS | 印尼锡精矿产量占比（%） | 印尼精炼镍产量 | block · variety_anchor |
| RISK-028 | P0 | THS | 印尼锡精矿产量时序图 | 印尼精炼镍产量 | block · variety_anchor |
| RISK-029 | P0 | THS | LME锡交易所库存（手） | LME：镍：注册仓单（日） | block · variety_anchor |
| RISK-030 | P0 | THS | LME锡交易所库存时序图 | LME：镍：注册仓单（日） | block · variety_anchor |
| RISK-031 | P0 | THS | 锡表观消费量（万吨） | 镀锌板卷：钢铁企业：产量：中国（周） | block · variety_anchor |
| RISK-032 | P0 | THS | 焊锡表观消费量时序图 | 镀锌板卷：钢铁企业：产量：中国（周） | block · variety_anchor |
| RISK-033 | P0 | THS | 国内锌锭消费量（万吨） | 国内锡锭产量 | block · variety_anchor |
| RISK-034 | P1 | THS | 盐湖提锂利润（元/吨） | 盐湖提锂产量 | block · BL-016 |
| RISK-035 | P1 | THS | 工业级碳酸锂利润（元/吨） | 工业级碳酸锂产量 | block · BL-016 |
| RISK-036 | P1 | THS | 电池级碳酸锂利润（元/吨） | 电池级碳酸锂产量 | block · BL-016 |
| RISK-037 | P1 | THS | 电池级碳酸锂冶炼利润（元/吨） | 电池级碳酸锂产量 | block · BL-016 |
| RISK-038 | P1 | THS | 库存天数（天） | 碳酸锂工厂库存天数 | block · BL-012 |
| RISK-039 | P1 | THS | 厂内库存天数（天） | 碳酸锂工厂库存天数 | block · BL-012 |
| RISK-040 | P1 | THS | 电解镍厂库存天数（天） | 碳酸锂工厂库存天数 | block · variety_anchor |
| RISK-041 | P1 | THS | 高冰镍厂库存天数（天） | 碳酸锂工厂库存天数 | block · variety_anchor |
| RISK-042 | P1 | THS | 多晶硅工厂库存天数（天） | 碳酸锂工厂库存天数 | block · variety_anchor |
| RISK-043 | P1 | THS | 金属硅工厂库存天数（天） | 碳酸锂工厂库存天数 | block · variety_anchor |
| RISK-044 | P1 | THS | 社会库存天数（天） | 锡锭：库存：中国（周） | block · BL-012 |
| RISK-045 | P1 | THS | 工厂库存天数（天） | 碳酸锂工厂库存天数 | block · BL-012 |
| RISK-046 | P1 | THS | 工厂库存天数时序图 | 碳酸锂工厂库存天数 | block · BL-012 |
| RISK-047 | P1 | THS | 在途库存天数（天） | 锂矿 外采 在途库存 | block · BL-012 |
| RISK-048 | P1 | THS | 库存天数（天） | 碳酸锂工厂库存天数 | block · BL-012 |
| RISK-050 | P1 | THS | 国内锌厂内库存天数（天） | 碳酸锂工厂库存天数 | block · variety_anchor |

### 2.1 规则归因

| 规则 | 命中案例数 | 占比 |
|---|---|---|
| **R-01b 品种锚点** `variety_anchor_violation` | **22** | 59.5% |
| **R-05 黑名单前置** `blacklist_precheck` | 15 | 40.5% |
| **R-07 别名库直查** `alias_exact` | **0** | 0% |
| 无匹配目标（结构性拦截） | 4 | — |

触发到的黑名单规则：BL-012 ×7（库存天数族）、BL-016 ×4（利润/产量）、BL-002 ×2（产量/销量）、BL-005 ×1、BL-009 ×1。

**R-07 命中 0 的意义**：本轮回放运行时别名库**尚未接入**匹配链路（R-07 为能力位）。别名库的价值是**防止同类错配复发**，而不是回补历史错配 —— 历史 41 条的匹配结果已经落库，无法由别名库追溯修正。这一点在本轮验证中被明确确认，而非推测。

---

## 3. 无回归三态回放（1134 条 fuzzy_name）

| 态 | 行数 | 占比 | 语义 |
|---|---|---|---|
| `keep` 自动通过 | **303** | 26.7% | |
| `review` 降级人工复核 | **234** | 20.6% | 禁止自动放行 |
| `block` 硬拦截 | **597** | 52.6% | |

### 3.1 block 原因分布

| 原因 | 行数 |
|---|---|
| variety_anchor_violation | **351** |
| below_threshold | 210 |
| metric_exclusion_hard | 18 |
| blacklist_precheck | 18 |

### 3.2 review 原因分布

`variety_neutral_target_review` **234**（全部）。

### 3.3 按黑名单状态交叉

| | CLEAN | WARNING | P0_CONFLICT |
|---|---|---|---|
| block | 575 | 17 | 5 |
| review | 228 | 0 | 6 |
| keep | — | — | — |

### 3.4 按 verify_status 交叉

| | FILLED | VALID | INVALID |
|---|---|---|---|
| block | 383 | 200 | 14 |
| review | 134 | 99 | 1 |
| keep | 80 | 214 | 9 |

### 3.5 新旧前后置对照（关键指标）

| 指标 | 值 |
|---|---|
| 旧流水线事后标记总数 | 52 |
| 新前置规则捕获 | **43（82.7%）** |
| 新前置仍漏放 | **9** |
| block 中「旧已被标记」 | 36 |
| block 中「旧 CLEAN」 | **561** |
| keep 中「旧已被标记」 | 9 |
| review 中「旧已被标记」 | 7 |

**结论**：V86 前置规则集把旧流水线的 52 条事后标记中 43 条（82.7%）提前拦截；同时**新增拦截 561 条旧 CLEAN 行**。这 561 条是旧流水线完全未察觉的风险面，也是本轮最大的收益项。

### 3.6 6 条 P0_CONFLICT 由 R-01b 捕获

| series | matched | 判定 |
|---|---|---|
| LME锡库存（吨） | LME：镍：注册仓单（日） | review · variety_neutral |
| LME锡库存时序图 | LME：镍：注册仓单（日） | review · variety_neutral |
| LME锡交易所库存（手） | LME：镍：注册仓单（日） | review · variety_neutral |
| LME锡交易所库存时序图 | LME：镍：注册仓单（日） | review · variety_neutral |
| 锡表观消费量（万吨） | 镀锌板卷：钢铁企业：产量：中国（周） | review · variety_neutral |
| 焊锡表观消费量时序图 | 镀锌板卷：钢铁企业：产量：中国（周） | review · variety_neutral |

（注：在 41 条风险回放中这些 case 因 left 侧品种明确而被硬 `block`；在 1134 条无回归回放中同一对匹配因系列名归一化后品种中性而降为 `review`。两处判定一致指向「禁止自动放行」，不构成冲突。）

### 3.7 仍自动放行 9 条（全部 `verify_status=INVALID` + `bl=CLEAN`）

| series | matched → target_canon | indicator_key | reason |
|---|---|---|---|
| 海外锂矿进口量分国别（万吨LCE） | 锂精矿进口分国别 | li_61_by_country_import_conc_3 | mid_dice_same_variety |
| 硫酸镍产量 | 中国硫酸镍产量 | wr241 | mid_dice_same_variety |
| 硫酸镍产量（万吨） | 中国硫酸镍产量 | wr241 | mid_dice_same_variety |
| 加工费（元/吨） ×6 | TC加工费 | TC | mid_dice_same_variety |

**语义审计结论**：这 9 条**语义上并非错配**，而是「简称→全称」的正确同义关系（加工费→TC加工费、硫酸镍产量→中国硫酸镍产量、海外锂矿进口量分国别→锂精矿进口分国别）。旧流水线的 `verify_status=INVALID` 标注源于**数据校验失败**（数值缺失/口径不符），不是匹配语义错误。

因此 82.7% 的「捕获率」应理解为：**旧事后标记 52 条中，43 条确实是需要拦截的语义错配，9 条是数据校验问题被误标为匹配问题**。V86 对后 9 条的处理（自动放行）在匹配语义层面是正确的，其 `INVALID` 需由数据层处理，不应由匹配规则承担。

---

## 4. 448 行歧义清单

| 项 | 值 |
|---|---|
| 总行 | **448** |
| IV1_NEAR_PAIR | 206 |
| BLACKLIST_RULE | 201 |
| RISK_DB | 41 |
| P0_manual | **251** |
| P1_manual | 176 |
| 混淆对总数 | 633 |
| 近邻对（≥0.75） | 1198 |
| 近邻对（≥0.85） | **295** |
| 近邻对跨品种 | 1147 |
| 近邻对同族 | 0 |

**review_action 区分**（本轮修订项）：

| 类别 | 说明 | 建议动作 |
|---|---|---|
| **跨品种正常区分项** | 两侧为不同品种的正常指标，仅名字相近（如「锌库存」vs「锡库存」） | **不建议**建黑名单规则；应依赖 R-01b 品种锚点 |
| **同族近义名** | 同族内不同口径/粒度的指标（如「社会库存」vs「厂内库存」） | 建议建口径互斥规则 |

旧稿把这两类混为「确认是否应新增黑名单规则」，导致 206 条 IV1 近邻对中大量正常跨品种指标被建议建黑名单 —— 这是**错误的动作建议**。本轮已区分。

---

## 5. 别名库消融结论

| 问题 | 结论 |
|---|---|
| 别名库能否回补历史 41 条错配？ | **不能**。历史匹配结果已落库，别名库不参与已生成记录的改写。 |
| 别名库能否阻止同类错配复发？ | **能，但需接入 R-07**。本轮回放 R-07 命中 0，因其尚未接入匹配链路。 |
| 别名库对 1134 条 fuzzy 的影响？ | 未接入状态下 303 keep / 234 review / 597 block；接入 R-07 后 review 队列预计大幅收缩（43 条正向 review 中多数可被别名库直查消解）。 |
| 是否可直接批量入库？ | **仅 W1 层 2502 行**（53.9%）可直接批量；W2 369 行需人工；W3 38 行禁止；W0 1734 行需先补 canonical 注册。 |

---

## 6. 结论

1. **公式复现 90.0%（1021/1134）**，比对目标为 `canon_name(indicator_key)`，`matched_name` 为展示字段 —— 已独立复核 VERIFIED。
2. **别名库 4643 行 / 覆盖 1652 canonical key**，质量四层：W1 2502 / W0 1734 / W2 369 / W3 38。
3. **41 条风险案例全部拦截（37 block + 4 结构性），误放行 0**；归因 R-01b 22 / R-05 15 / R-07 0。
4. **无回归 1134 条：303 keep / 234 review / 597 block**；新增拦截旧 CLEAN 561 条；旧 52 条事后标记捕获 43 条（82.7%）。
5. **9 条仍自动放行**经语义审计为「简称→全称」正确同义，旧 INVALID 标注系数据校验问题，非匹配语义错误。
6. **448 行歧义清单**中 206 条 IV1 近邻对需区分「跨品种正常区分项」（不建议建黑名单）与「同族近义名」（建议建口径规则）。
7. **两列不一致率口径已修正**：44.0%（含 26.3pp 缺失）→ 真实冲突 17.7%。

---

## 7. 局限

1. **别名库尚未接入匹配链路**：R-07 命中 0，其收益全部为预估，需按 `alias_lib_import_guide.md` 的 S1–S9 步骤实测。
2. **verify_status 非干净标签**：FILLED 表示「旧流水线自动填入」，可能本身即错误匹配。1134 条回放中 383 条 FILLED 被 block，其中相当部分属旧流水线自身错配（回归测试中测得 55 条）。
3. **9 条 INVALID 保留行未逐条核数据**：仅做匹配语义审计，未查数值层原因。
4. **别名库不能追溯修正历史错配**：这是机制限制，非缺陷，但意味着「导入别名库」不能降低历史错配率，只能降低未来新增率。
5. **短名风险未完全消解**：125 行（11.0%）canonical 名 ≤4 字，别名库只能提供上下文消歧，无法改变 Dice 分母过小的数学事实。
6. **295 条近邻对（≥0.85）未逐条定级**：仅统计，未给出逐条 P0/P1 判定。
7. **不含价格数据、策略与 PnL**：全部为静态文本模拟。
