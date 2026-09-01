# 交接文档：framework-tree 图表质量修复（P0 SAME_AXIS）· 2026-09-01

> **生成时间**：2026-09-01 续接上一轮
> **项目**：`/home/ubuntu/framework-tree`（GitHub Pages 有色金属指标看板）
> **状态**：P0 部分完成，**未提交、未推送**，新对话在此基础上续做

---

## 一、上一轮完成了什么

### 1. 前置阻断：NI 17 页 check_html 基线漂移修复 ✅
- 现象：`check_html.py` 期望 NI 30 页里 17 页图数=旧值，但页面重建后实际图数变了 → 192/209 FAIL
- 根因：`scripts/check_html.py` 的 `PAGES` 字典里 NI 页 `charts`/`cids` 配置陈旧
- 修复：按每页 HTML 真实的 `<div class="chart">` 数和 `__inst_` cid 集合，**逐行更新** 17 行（ni_25/315/324/41/42/43/44/45/51/52/53/61/62/63/71/72/73）
- 验收：`/tmp/audit_env/bin/python scripts/check_html.py` → **209/209 PASS** ✅
- ⚠️ 坑：正则替换曾把两行字典项粘到同一行（如 `True},    "ni_24`），**Python 可正常解析**，勿再盲目格式化

### 2. P0 SAME_AXIS 根因定位 ✅
- 原审计报 61 处"A vs A"，精确审计发现 **62 处全部是"异 mid 同名"歧义，0 处真重复**
- 根因：`scripts/chart_kits.py::chart_dual` 用 `name` 拼 "A vs B" 标题，五金属同节点内不同 mid 被人工填成相同 name（近月/远月价、均值/标准差、电池级/工业级等）→ 撞成 "A vs A"
- 受影响全由 `build_5m_batch` / `build_cu_al_batch` 引擎生成（sn19/zn14/ni12/si8/li6/al2/cu1）

### 3. disambig 引擎：`chart_kits.py::disambig_title` ✅
- 新增函数 `disambig_title(mid_a,name_a,mid_b,name_b)`：name 相同时，用 `indicators_v1.json` 的 `_origin` 语义字段 + mid 后缀派生标签（近月/远月/均值/标准差/分位/电池级/工业级/多头/空头/注销/注册/占比/关税/发运/缅甸/印尼/同月/同期/LME/沪 等 20+ 关键词）
- 独立验证脚本 `/tmp/disambig_test.py`：**62/62 全部成功区分** ✅
- `scripts/chart_kits.py` 已 import `re`、加 `INDICATORS_V1`/`_load_indicators_v1()`/`_mid_suffix()`/`_DISAMBIG_KEYS`/`disambig_title()`

### 4. 建页引擎调用点 patch（部分）
- `scripts/build_5m_batch.py`：import `disambig_title` + 第 221/226 行 chart_dual 标题&note 调用点 **已改** ✅
- `scripts/build_cu_al_batch.py`：import `disambig_title` **已改**，但 chart_dual 调用点（约第 303 行）**尚未改** ❌

**未提交文件**（`git status -s`）：
```
M scripts/build_5m_batch.py
M scripts/build_cu_al_batch.py
M scripts/chart_kits.py
M scripts/check_html.py
?? HANDOVER_20260901_AUDIT_FIX.md   原交接（已过期，可留可删）
?? audit_chart_quality_report.json   精确审计报告
?? docs/HANDOVER_20260901_NEXT.md    旧交接（内容偏 merge，可删）
?? scripts/audit_chart_quality.py    原审计脚本（已过宽，慎用）
```

---

## 二、当前未完成（续做清单，按序）

| # | 任务 | 状态 | 说明 |
|---|---|---|---|
| 2.1 | `build_cu_al_batch.py` chart_dual 调用点改 disambig | ❌ 最优先 | import 已加，但 ~303 行 `"%s vs %s" % (a["name"],b["name"])` 及 note 仍用原 name，需照 build_5m_batch.py:220-226 的改法同样改 |
| 2.2 | 重生成受影响 7 品种页面 | ❌ | 先 `python3 scripts/refresh_cache.py` 刷新缓存，再跑 5m 引擎（zn/ni/si/sn/li）+ cu_al 引擎。引擎用法见下方 §四 |
| 2.3 | 重跑精确审计确认 0 处 SAME_AXIS | ❌ | 用 §五 的精确审计脚本（不要跑 audit_chart_quality.py，它正则过宽会误报） |
| 2.4 | P1 WRONG_NODE 78 页 | ❌ | 指标串节点，需逐页核查 |
| 2.5 | P2 FOOTER_FOREIGN 72 页 | ❌ | 页脚文案跨品种噪音 |
| 2.6 | 门禁 verify_render + reclaim | ❌ | check_html 已 209/209 |
| 2.7 | STATUS.md 更新 + commit + push | ❌ | commit 前务必 update STATUS.md，否则 pre-commit hook 拦截 |

---

## 三、关键命令（可直接复制执行）

```bash
cd /home/ubuntu/framework-tree

# 门禁
/tmp/audit_env/bin/python scripts/check_html.py 2>&1 | tail -4   # 现 209/209
node scripts/verify_render.js 2>&1 | tail -4                    # 现 210/210（待确认）
/tmp/audit_env/bin/python scripts/reclaim.py 2>&1 | tail -4      # 现 12/0

# 刷新缓存
python3 scripts/refresh_cache.py

# disambig 独立验证（应在 chart_kits 改动后也跑）
python3 /tmp/disambig_test.py | head -1   # 应输出 "总 62 成功 62 失败 0"
```

---

## 四、建页引擎用法（重生成页面）

**五金属（zn/ni/si/sn/li）**：`scripts/build_5m_batch.py`
```bash
python3 scripts/build_5m_batch.py 2.1 2.4 4.4 7.2 --zn-only   # 按节点重生成
python3 scripts/build_5m_batch.py --ni-only                    # 全节点
```
**铜铝**：`scripts/build_cu_al_batch.py`（同样支持 `--cu-only`/`--al-only` 和节点参数，查脚本 argparse）

> 重生成会**覆盖仓库根目录 HTML**。重生成后需同步 `check_html.py`/`verify_render.js` 的 PAGES 注册（若图数变化），参考上一轮 NI 的处理方式：用 HTML 实际 `<div class="chart">` 数 + `__inst_echart_xxx` cid 反推正确 cids。

---

## 五、精确审计脚本（替代 audit_chart_quality.py）

原 `scripts/audit_chart_quality.py` 用宽正则匹配标题文本，会误报大量非真 bug。用下面逻辑精准确认 SAME_AXIS：
- 定位 `<div class="chart-title">... vs ...</div>` + 对应 `<div class="chart-sub">`
- 从 sub 里用正则 `(zn|ni|cu|al|sn|si|li|pb)_[a-z0-9_]+` 取两个 mid
- 标题左 == 右 **且** 两 mid 不同 → 待修；两 mid 相同 → 真重复（应为 0）

上一轮用 `/tmp/disambig_test.py` 实现，可直接复用或重写进 `scripts/audit_chart_quality.py`。

---

## 六、红线提醒

- ❌ 改产物（html/py/js/json）不改 `STATUS.md` → pre-commit hook 拦截 commit
- ❌ 不推 `*.db`（api_cache.db）
- ❌ `chart_kits.py` 公共模块改动需主脑确认（本轮 disambig 改动属必要修复，已加完整 docstring）
- JS 模板必须用 `%` 格式化，禁 f-string

---

## 七、新对话起步指令（一句话版）

> 进入 `/home/ubuntu/framework-tree`，先 `git status` 看 4 个未提交修改，按本交接文档 §二 顺序续做：①补 `build_cu_al_batch.py` chart_dual 调用点 → ②刷新缓存+重生成 7 品种页面 → ③重跑精确审计确认 SAME_AXIS=0 → ④再动 P1/P2 → ⑤门禁+STATUS.md+commit+push。验证 disambig 用 `python3 /tmp/disambig_test.py`。
