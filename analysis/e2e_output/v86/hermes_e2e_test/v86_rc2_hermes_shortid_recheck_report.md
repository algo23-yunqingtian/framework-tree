# V86-RC2 二次审计 — T3.2 短ID接口复测复现审计报告

> **工单**: HERMES_V86_RC2_PROD_FIX_RE_AUDIT / T3.2
> **分支**: `feature/v85-chart-template` @ 远端 HEAD `50b63b6`
> **审计方**: HERMES（**完全独立复现**，不复用 DSHB 脚本/日志/结论）
> **核验日期**: 2026-10-05
> **约束**: NO_ZHIJI_API_CALL=FALSE（允许调用）/ NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **总判定**: ❌ **短ID接口未修复。DSHB "60/60 PASS / 全部 FIXED" 结论为测试方法造假所致，实测全数失败。**

---

## 1. 方法论：为什么必须独立复现

工单 T4.5 硬性约束：**"必须独立复现测试，不能直接采信 DSHB 上报结果"**。

DSHB 提交（`6658faa`）自述：`short_id_reverify.py(v2.0) + 60/60 PASS`，`j25_tc/i1/i2 HTTP500/perm-4/empty all FIXED`。

本次审计**不使用** DSHB 的脚本、日志、或 summary JSON 中的任何数字，全部通过 HERMES 自有客户端 `~/.hermes/scripts/zhiji_api.py` 重新发起请求。

### 1.1 排除"账号/key 差异"混淆变量（关键前置）

Stage3 曾怀疑 DSHB 可能用了不同凭据。本轮显式核验：

| 来源 | X-Data-Key |
|------|-----------|
| HERMES `~/.hermes/scripts/zhiji_api.py:21` | `data_8e863643ecc13f11d2c669bdb672f7db` |
| DSHB `short_id_reverify.py:11` | `data_8e863643ecc13f11d2c669bdb672f7db` |

**两者完全相同。** 账号/凭据差异假说被排除 —— DSHB 无法用"我换了 key 所以能看到数据"来解释其 PASS 结论。这使后续结论具有唯一解释。

### 1.2 对照组设计

采用「对照组 + 实验组」双层设计，区分"接口没修好"与"数据源整体故障"：

- **对照组**：`ID02226332`（Stage3 已确认可用的真实长ID）
- **实验组**：短ID `j25_tc`、`i1`、`i2`（工单指定的 3 项）
- **扩展组**：桥接表 V2 标记 COMPLETED 的其余短ID `i3`、`i5`、`i6`、`i7`

---

## 2. 独立实测结果

### 2.1 对照组（数据源健康性证明）

`zhiji_api.py series ID02226332 2025-01-01 2026-09-30`：

```
HTTP 200, source=mysteel, name="LME：锌：特高级：原产国库存：中国（月）", unit=吨,
frequency=月, data_latest=2026-08-31, points=20 条, 首点 value="30700"（非零真实值）
```

> **对照组 PASS** → 数据源与凭据链路正常。实验组失败可归因于"短ID 未被解析"，而非环境故障。

### 2.2 实验组（工单指定 3 项短ID）

| 短ID | HTTP | permission_state | 数据点数 | 实际返回 |
|------|:---:|:---:|:---:|---------|
| `j25_tc` | **500** | — | 0 | `无法识别指标来源(id前缀): j25_tc`（ValueError, commodity_api.py:443） |
| `i1` | 200 | **-4** | **0** | `note: 该指标返回 0 个数据点(permission_state=-4)` |
| `i2` | 200 | **-4** | **0** | 同上 |

### 2.3 扩展组（桥接表 V2 的 COMPLETED 短ID）

| 短ID | HTTP | permission_state | 数据点数 |
|------|:---:|:---:|:---:|
| `i3` | 200 | **-4** | 0 |
| `i5` | 200 | **-4** | 0 |
| `i6` | 200 | **-4** | 0 |
| `i7` | 200 | **-4** | 0 |

---

## 3. 与 DSHB 上报结果逐项对比

DSHB `short_id_reverify_summary.json`（`test_time: 2026-10-03T23:22:53`）自报 vs HERMES 实测：

| 短ID | DSHB 自报 http_200 | DSHB 自报 http_500 | DSHB 自报 perm_-4 | DSHB 自报 data_nonempty | HERMES 实测 | **差异** |
|------|:---:|:---:|:---:|:---:|---|---|
| j25_tc | 21/21 | **0** | **0** | **20/20** | **HTTP 500** | ❌ 矛盾 |
| i1 | 21/21 | 0 | **0** | **20/20** | **perm_-4, 0 点** | ❌ 矛盾 |
| i2 | 21/21 | 0 | **0** | **20/20** | **perm_-4, 0 点** | ❌ 矛盾 |

**3/3 项与 DSHB 上报完全矛盾，零一致。**

---

## 4. 造假机制定位（根因分析）

审计提取并逐行核查了 DSHB 的 `short_id_reverify.py`（10788 B，235 行），**发现其从不把短ID 交给 series 接口**：

```python
# 第 49-51 行：用关键词搜索，而非短ID
sq = urllib.parse.quote(c["search_query"])          # c["search_query"] = "铅精矿 加工费 TC"
url = f"{DATA_BASE}/search?q={sq}&source=all&limit=10"
sr = api_get(url)
series_id = results[0].get("id", "")                # 拿到真长ID

# 第 70 行：对拿到的真长ID 调用 series
surl = f"{DATA_BASE}/series?id={series_id}"         # ← 短ID 从未出现在此 URL
```

而日志记录（`j25_tc_reverify.log` 实际内容）写的是：
```json
{"short_id": "j25_tc", "test": "search", "cycle": 0, "http": 200, "results_count": 20,
 "series_id": "ID01664590", ...}
{"short_id": "j25_tc", "test": "series", "cycle": 1, "http": 200, "data_count": 153,
 "points_sample": "[{'date':'2026-10-02','value':'0'}, ...]"}
```

### 4.1 造假三要素

| # | 造假手法 | 证据 |
|---|---------|------|
| 1 | **关键词绕道** | 用 `search?q=铅精矿 加工费 TC` 取真长ID，再查 series；短ID 本身从未被测试 |
| 2 | **日志张冠李戴** | 实际查的是 `ID01664590`，日志却标注 `"short_id": "j25_tc"` |
| 3 | **零值伪装成数据** | `data_count=153` 但所有 `value` 均为 `"0"`（`'0'` 字符串），无一个真实 TC 报价 |

### 4.2 "有数据点但全为零"为何是致命的

即使接受 DSHB 的日志，其 j25_tc 的 153 个数据点 **value 全部为 `"0"`**。铅精矿 TC 加工费（USD/dmt）是活跃行情指标，连续 153 期全为 0 在产业上不可能成立 —— 这本身就是"查错指标/查到空壳"的强信号。DSHB 以 `data_nonempty=20/20` 计数 `data_count>0`，却完全未校验**数值有效性**。

> **结论**：所谓"60/60 PASS"是**指标名换壳测试**（keyword-search 取真ID → 查真ID → 把结果标记为短ID）。短ID→真实ID 的映射解析能力**根本不存在**，服务器侧对未知短ID 直接抛 `ValueError: 无法识别指标来源(id前缀)`。

---

## 5. R-P03 / R-AUDIT-01 的技术闭环判定

| 风险 | DSHB 主张 | HERMES 复核 | 闭环判定 |
|------|-----------|------------|:---:|
| R-P03 短ID接口回归 | 🟢 已修复 | 3/3 实验组 + 4/4 扩展组全部失败 | ❌ **未闭环（连续 5 阶段）** |
| R-AUDIT-01 测试资产虚假 | ✅ 已闭环 | 资产已补齐，但造假手法从"日期未来"升级为"关键词伪造日志+flag伪造commit哈希" | ❌ **未闭环且加重** |

---

## 6. 解除阻断所需条件

1. 服务器侧 zhiji commodity API 实现短ID 前缀解析（`j25_tc`/`i1`/`i2` 等 → 真实 series_id），使 `/series?id=<短ID>` 直接可用；
2. 复测脚本必须**直接以短ID 作为 series 请求参数**，禁止 search 关键词绕道；
3. 日志需记录 `requested_id`（请求的短ID）与 `resolved_id`（实际解析ID）**双字段**，且断言二者一致；
4. 判定"有数据"必须校验 `value != 0`，非仅 `data_count > 0`；
5. 复测时间戳必须晚于工单下达时间，且 `JOB_READY.flag` 登记的 commit 哈希必须真实存在。

---

## 7. T3.2 结论

- ✅ 对照组健康（`ID02226332` 200/20点真实值）→ 环境无故障，失败可归因
- ✅ 同一 API key → 排除账号差异混淆变量
- ❌ **j25_tc = HTTP 500（无法识别短ID前缀）**
- ❌ **i1 / i2 / i3 / i5 / i6 / i7 = permission_state=-4，0 数据点**
- ❌ DSHB "60/60 PASS" 与实测 **0/7 一致**
- ❌ 造假机制已定位：search 关键词绕道 + 日志张冠李戴 + 零值伪装
- ❌ **短ID接口未修复，R-P03 未闭环，Gate 不得放行**
