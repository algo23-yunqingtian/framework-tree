# alias_import_validation_report.md — 别名库导入链路校验报告

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY · T2.3 |
| 脚本 | `dshe_alias_integrate_test/alias_lib_import_validate.py`（可运行，支持 `--strict`） |
| 结果 | `alias_import_validation_result.json`（8,110 bytes） |
| 判定引擎 | `build_alias_library.py` 第 1..655 行，MD5 `d375f963678d1e89c7e9949805f8433f` |
| 生成时间(UTC+8) | 2026-10-01 12:28:01 |
| 只读声明 | **不修改** `indicator_alias_library.csv` / `indicators_v1.json`；不调用 zhiji API；导入为内存模拟 |
| **总体判定** | **import_ready = FALSE**（BLOCK 1 / WARN 2 / INFO 1） |

被校验文件：
- 别名库 `alias_lib_full_audit/indicator_alias_library.csv` — 1,081,339 bytes，MD5 `e9989c2938b1707739f85e6085e91414`，**4643 行 × 23 列**
- `data/indicators_v1.json` — 713,207 bytes，MD5 `ebcbd9a7cf69830384c696607bfeda76`，**1658 键**

---

## 1. 九项校验结果

| ID | 校验项 | 级别 | 结果 |
|---|---|---|---|
| V1 | CSV schema / 主键唯一 / 空值 | **PASS** | 4643 行；23 列齐全；`alias_id` 重复 0；`alias_norm` 空 0；`alias_name` 空 0 |
| V2 | `alias_norm` 归一化口径一致性 | **PASS** | 4643/4643 与 `norm_full(alias_name)` 完全一致，**漂移 0** |
| V3 | `canonical_key` 存在性 | **PASS** | 3300 个键 token，**缺失 0**（全部在 iv1 1658 键内） |
| V4 | 四层质量分层复算 | **PASS** | 复算与 `relation` 列一致，`relation × review_flag` 不自洽 **0 行** |
| V5 | B1 八道门禁 G1–G8 | **WARN** | 候选 2502 → 通过 2502 → 剔除 0（详见 §3.1） |
| V6 | 幂等性（与 iv1 现有 alias 比对） | PASS | iv1 现有 aliases 字段 **0** 条；1226 行的 `alias_name` 已是某 iv1 正名 |
| V7 | 冲突与循环 | **BLOCK** | `alias_norm` → 多个原子键 **165 行**；`canonical_name` → 多个原子键 170 个（详见 §3.2） |
| V8 | 非法字符 / 超长 | PASS | 空白与控制符 0 行；超 120 字符 0 行；实测最长 78 |
| V9 | B1 写入预演 | **PASS** | 2502 通过 → 目标键 1650 个，**计划写入 2253 条**，已存在跳过 249，目标键缺失 0 |

### V4 分层复算明细

| 层级 | 行数 | 占比 | 对应 relation |
|---|---|---|---|
| W1_可靠同义 | 2502 | 53.9% | `synonym_merge` |
| W0_待注册 | 1734 | 37.3% | `unregistered` |
| W2_存疑 | 380 | 8.2% | `synonym_with_confusable_neighbor` 215 + `canonical_conflict` 165 |
| W3_明确错误 | 27 | 0.6% | `confusable_warn` |

`review_flag` 分布：`auto` 2502 / `register_pending` 1734 / `manual_review` 407（=215+165+27）。**relation 与 review_flag 一一对应，无例外。**

---

## 2. 可执行导入规模

```
B1 候选 2502  →  门禁通过 2502 (100.0%)
            →  单键行 2502 / 复合键行 0
            →  目标 canonical 键 1650 个
            →  计划写入 aliases  2253 条
            →  已存在跳过        249 条（幂等命中）
            →  目标键缺失          0
            →  iv1 中尚无 aliases 字段的键 1654 个
```

即：B1 批次实际向 iv1 新增 **2253 条别名映射**，其中 **9.3%（249）为重复映射**（同名不同写法已存在）。

---

## 3. 阻断项与需人工处理项

### 3.1 V5 门禁缺乏独立筛查力（WARN）

G1–G8 对全部 2502 条 B1 候选**无一剔除**。原因：`review_flag = auto` 标签在上游已等价编码了这 8 项条件（`relation=synonym_merge` / 无 `canonical_conflict` / 无 `confusable_warn` / 键存在 / 无黑名单命中 / 无风险案例关联 / 无歧义命中 / `confidence` 达标）。

**门禁与标签不是独立信号，100% 通过率不代表质量高。** 建议补一道独立抽检：从 B1 随机抽样 100 条人工核对，若错误率 > 2% 则暂停导入。当前无该抽检数据，**此为未知风险**。

### 3.2 V7 `alias_norm` → 多个原子键（BLOCK，165 行）

同一个归一化别名形态同时被绑定到 2 个以上不同 canonical 键，导入后该别名指向不唯一：

| alias_norm | 指向的原子键 |
|---|---|
| `SHFE:铝:主力合约:收盘价(日` | `al_00_close_front` / `al_53_close_front` |
| `LME:铝:3个月合约:结算价(日` | `al_23_lme_settle` / `al_24_lme_settle` |
| `国际铝业协会:原铝:产量:全球(月` | `al_2_output_2` / `al_312_global_output` |
| `氧化铝:净进口数量:中国(月` | `al_314_alumina_net_imp` / `al_3_import_alumina` |

关联统计：
- `distinct_canonical_names` 1239，其中 **170 个** `canonical_name` 对应多个不同原子键（同一正名被多个 key 声明，多为主/分位数等孪生 key）。
- `distinct_alias_norm` 2882（即 2882 个形态有 canonical 绑定，另 1761 行为 unregistered）。
- `alias_norm_is_self_canonical` 1230 —— alias 即自身 canonical 正名的正常自引用，非冲突。
- **真互指环（alias_norm 指向与本行键集合完全不相交的其他 canonical）= 0**。上一轮版本报告的 165 条「互指环」为复合键比较口径错误所致，已修正为原子键比较后清零，特此更正。

**处置建议**：165 行导入前必须逐条裁定唯一归属；可直接复用上一轮 `canonical_conflict` 165 行的复核结论（两者高度重叠，均为孪生 key 争用）。

---

## 4. 结论

| 项 | 判定 |
|---|---|
| 结构完整性（V1/V2/V8） | 全绿，别名库自身无格式/口径缺陷 |
| 键引用完整性（V3） | 全绿，0 悬挂键 |
| 分层一致性（V4） | 全绿，relation 与 review_flag 完全自洽 |
| 门禁有效性（V5） | **无效**：与标签等价，无独立筛查力 |
| 冲突检测（V7） | **阻断**：165 行别名归一不唯一 |
| 写入可执行性（V9） | 可执行：2253 条计划写入，0 目标缺失 |
| **是否可立即导入** | **否**（需先清 165 行冲突 + 补抽检） |

**导入前最小必要动作（估算人工量）**
1. 裁定 165 行 `alias_norm` 唯一归属 —— 约 1–2 人天。
2. B1 抽检 100 条（因 V5 无独立筛查力）—— 约 0.5 人天。
3. 清理 249 条重复映射（脚本可自动）—— 0 人工。

完成上述 3 项后可执行 **2253 条别名写入**；其余 2141 行（`register_pending` 1734 + `manual_review` 407）不在本批次范围内。
