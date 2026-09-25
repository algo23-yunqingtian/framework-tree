# 交付物⑤：语义邻近指标人工判定清单（pb_* ↔ i*）

> 工单：DSH_B_MERGE_HIST_IND_P3_REV | 日期：2026-09-24

---

## 判定概况

| 指标 | 数值 |
|------|------|
| pb_* 总数 | 472 |
| i* 总数 | 41 |
| 语义邻近匹配 | 472 |
| 判定为业务重复 | 0 |
| 判定为独立指标 | 472 |

---

## 判定结论

**pb_*与i*指标ID无交集（zhiji_id交集=0），所有匹配均为独立指标，非业务重复。**

原因：i*为PB旧版编号体系（41条），pb_*为PB新版规范ID体系（70条），两者是同一品种的不同指标集合。

---

## Top语义邻近对（仅展示名称高度相似的案例）

| i* Key | pb_* Key | 相似度 | 判定 |
|--------|----------|--------|------|
| `i30` | `pb_45_aux` | 51 | INDEPENDENT_INDICATOR |
|   i*: LME: 铅: 非注册仓单库存: 阿联酋: 迪拜: 日度
|   pb: LME: 铅: 非注册仓单库存: 总计: 日度
| `i26` | `pb_44_aux` | 33 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅蓄电池企业成品库存: 月度
|   pb: SMM: 电解铅冶炼企业成品库存: 月度
| `i26` | `pb_44_aux_2` | 33 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅蓄电池企业成品库存: 月度
|   pb: SMM: 再生铅冶炼企业成品库存: 月度
| `i32` | `pb_43_aux` | 27 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅锭五地社会库存: 广东: 周度
|   pb: SMM: 铅锭五地库存变化: 周度
| `i33` | `pb_43_aux` | 27 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅锭五地社会库存: 江苏: 周度
|   pb: SMM: 铅锭五地库存变化: 周度
| `i34` | `pb_43_aux` | 27 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅锭五地社会库存: 浙江: 周度
|   pb: SMM: 铅锭五地库存变化: 周度
| `i35` | `pb_43_aux` | 27 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅锭五地社会库存: 天津: 周度
|   pb: SMM: 铅锭五地库存变化: 周度
| `i36` | `pb_43_aux` | 27 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅锭五地社会库存: 上海: 周度
|   pb: SMM: 铅锭五地库存变化: 周度
| `i21` | `pb_45_aux` | 24 | INDEPENDENT_INDICATOR |
|   i*: LME: 铅库存分仓库: 新加坡: 注册仓单: 日度
|   pb: LME: 铅: 非注册仓单库存: 总计: 日度
| `i30` | `pb_23_aux` | 24 | INDEPENDENT_INDICATOR |
|   i*: LME: 铅: 非注册仓单库存: 阿联酋: 迪拜: 日度
|   pb: LME: 铅: 现货价: 日度
| `i26` | `pb_44_aux_3` | 21 | INDEPENDENT_INDICATOR |
|   i*: SMM: 铅蓄电池企业成品库存: 月度
|   pb: SMM: 再生铅冶炼企业原料库存: 月度
| `i28` | `pb_21_aux` | 21 | INDEPENDENT_INDICATOR |
|   i*: SHFE: 铅: 库存周报: 本周库存期货: 周度
|   pb: SHFE: 铅: 主力合约: 收盘价: 日度
| `i28` | `pb_21_aux_2` | 21 | INDEPENDENT_INDICATOR |
|   i*: SHFE: 铅: 库存周报: 本周库存期货: 周度
|   pb: SHFE: 铅: 主力合约: 收盘价: 日度
| `i28` | `pb_21_aux_4` | 21 | INDEPENDENT_INDICATOR |
|   i*: SHFE: 铅: 库存周报: 本周库存期货: 周度
|   pb: SHFE: 铅: 六月合约: 成交量: 日度
| `i28` | `pb_21_aux_6` | 21 | INDEPENDENT_INDICATOR |
|   i*: SHFE: 铅: 库存周报: 本周库存期货: 周度
|   pb: SHFE: 铅: 一月合约: 持仓量: 日度