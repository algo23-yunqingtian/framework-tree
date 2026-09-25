# framework-tree 三次复审报告（等待 F3 修复 · 前置未满足）

> 2026-09-13 20:50 · 分支 `origin/indicator-correction-win` HEAD=`8b513fc` · 全程只读审计
> 复审目标：等待 Dsharnes-B 提交 F3 缺陷修复 commit 后复核
> **结论：❌ 前置未满足 —— Dsharnes-B 未提交本次修复 commit，无新改动可复审**

---

## 一、一句话结论

**「待二次修复」**。远端 `indicator-correction-win` 最新提交仍为 `8b513fc`（上一轮我的复审报告），`267614d` 之后**没有任何新的修复提交**。F3 两项 P0 JS 回归、U2 别名新增、U4 死代码清理均**保持未修复状态**，`verify_render` 仍为 **140/224**（净损 30 页未回补）。PB 流水线**继续暂停**，简版→完整版任务书替换**未执行**。

---

## 二、复审范围执行情况

| 编号 | 复审项 | 执行状态 |
|---|---|---|
| P0 | F3-回归1 `__tgl` 引号 | ⚠️ 执行（基线复算），**未修复** |
| P0 | F3-回归2 `getElementById` ID 同步 | ⚠️ 执行（基线复算），**未修复** |
| P0 | `verify_render ≥ 170/224` | ⚠️ 执行，**140/224 未达标** |
| P0 | `check_html.py` 新增 JS 引用一致性检查 | ⚠️ 执行，**未新增** |
| P1 | U2 SHFE/上期所 别名真实新增（看 git diff） | ⚠️ 执行，**新增 0 条** |
| P1 | U4 清理 `EXCHANGE_WHITELIST` 死代码 | ⚠️ 执行，**仍为死代码** |
| 回归 | F1/F2/U1/U3 快速回归 | ⚠️ 执行，通过（沿用实测） |

> 「执行」= 在 `8b513fc`（代码态等价 `267614d`）上重跑实测，确认缺陷未变；
> 未提交新 commit ⇒ 无任何可评审的增量修复。

---

## 三、实测证据（只读 worktree `/tmp/wt_8b513fc` @ `8b513fc`，审完已清理）

### 3.1 前置判定：无新 commit

```
git log --oneline -5 origin/indicator-correction-win
8b513fc  [DOC] 三次复审报告(审267614d·待二次修复)     ← 最新，审计产出
267614d  fix(F1-F3+U1-U4): 前端残余修复+上游修复        ← 被审对象（上轮已审）
b400023  [DOC] 二次修复复审报告(前置受阻)
```

全库跨分支检索 `F3`/`tgl`/`getElementById` 关键词，**无任何新的修复提交**（`origin/main` 最新 `404f7ee` 为角色定义文档，与本次无关）。

### 3.2 P0-1 `__tgl` 引号嵌套 —— ❌ 未修复

```
grep -oh '__tgl("' pb_*.html | wc -l  →  40        （目标 0）
grep -oh "__tgl('" pb_*.html | wc -l  →  5
grep -c '__tgl("' pb_*.html | grep -v ':0'        →  26 个文件各 1 处
```

验收口径 `grep -c '__tgl("' pb_*.html` = **0** → **实测 40，未通过**。属性值仍会提前终止，按钮点击仍抛异常。

### 3.3 P0-2 `getElementById` 旧命名 —— ❌ 未修复

```
grep -oh "getElementById('echart_[0-9]" pb_*.html | wc -l  →  90   （目标 0）
```

验收口径 = **0** → **实测 90，未通过**。div 名为 `echart_pb_*` 而 init 仍找旧 id，返回 null，整页图表不渲染。

### 3.4 P0 门禁 —— ❌ 未回绿

| 门禁 | `1def0f2` 基线 | 本次实测 | 判定 |
|---|---|---|---|
| `scripts/verify_render.js` | 170/224 | **140/224** | ❌ 未达 ≥170，净损 30 页未回补 |
| `scripts/check_html.py` | 169/223 | **169/223** | ⚪ 持平（不回退，但盲区未补） |

### 3.5 P0 `check_html.py` JS 引用一致性检查 —— ❌ 未新增

```
grep -n "getElementById\|__tgl\|引用一致" scripts/check_html.py
12:   6. 公共 JS 关键函数存在（__seasonalize / __tgl / resize 监听）
878:  COMMON_JS_TOKENS = ["function __seasonalizeByYear","function __tgl","addEventListener('resize'"]
```

仅校验 `__tgl` **函数定义存在**，**无** div-id ↔ `getElementById`/`__tgl` 参数引用一致性检查。本次回归仍无法被静态检出，P2 盲区原样保留。

### 3.6 P1 U2 SHFE/上期所 别名 —— ❌ 无真实新增

`git show 267614d -- docs/alias_metadb/thsh_zhiji_alias_map.json` 对该 JSON 的**唯一实质改动**为 `_meta` 段新增 3 行元信息：

```diff
-    "coverage_note": "覆盖已注册指标+步三最终判定结果"
+    "coverage_note": "覆盖已注册指标+步三最终判定结果",
+    "updated": "2026-09-13 19:30",
+    "shfe_alias_update": "U2: added 0 SHFE/上期所 aliases"
```

**别名条目新增 0 条**（元信息自认 "added 0"）。`上期所` 全库仅 **4** 处（上轮 3 处，本轮 +1 为上述注释串，非别名条目）。未覆盖 70 条 SHFE 指标，STATUS.md 归因仍不成立。

### 3.7 P1 U4 `EXCHANGE_WHITELIST` 死代码 —— ❌ 未清理

```
grep -rn "EXCHANGE_WHITELIST" . --include=*.py
./scripts/_fix_all.py:254:EXCHANGE_WHITELIST = {
./scripts/task3_hallucination_clean.py:39:EXCHANGE_WHITELIST = {
```

仅 2 处**定义**、**0 处引用**。`scripts/_fix_all.py` 为一次性脚本（`267614d` 新增，447 行，未纳入流水线），其内定义同样未被调用。

实际生效的仍为 `CROSS_EXCHANGES`（`task3_hallucination_clean.py:53`，第 108 行由 `classify_indicator` 调用，仅被 `return "cross_commodity"` 分支消费）。二者语义互斥：

| 品种 | `EXCHANGE_WHITELIST`（死） | `CROSS_EXCHANGES`（活） |
|---|---|---|
| LI | `["GFEX"]` | `["COMEX","SHFE","上期所"]` |
| PB | `["SHFE","上期所"]` | `["COMEX","GFEX"]` |
| NI | `["SHFE","上期所","LME"]` | `["COMEX","GFEX"]` |

白名单语义（允许集）与黑名单语义（禁止集）**恰好互补**，功能碰巧正确，但维护风险高——改一处不同步另一处即产生隐性缺陷。交易所过滤逻辑**非唯一**。

### 3.8 快速回归（F1/F2/U1/U3）—— ⚪ 通过（沿用实测）

未提交新 commit ⇒ 代码态与 `267614d` 完全一致，上一轮已实测通过项无需重复大规模复测：

| 项 | 上轮实测结论 | 本轮 |
|---|---|---|
| F1 R1 | ⚪常规节点页残留 =0；🟢155 = 95 无关键词命中 + 60 跨板块主图 | ⚪ 通过 |
| F2 R3 | 覆盖率 555/452 = 122.8%；555+0+703+59=1317；扫描 1317/1379=95.5% | ⚪ 通过 |
| U1 C1 | CU 129 条 B=74/C=55/A=0 → 57.36%；`score>=4→matched` 生效 | ⚪ 通过 |
| U3 C3 | 198 文件/5356 条/剔除 372(6.9%)/跨品种 9 条；4 条 COMEX 漏检 4/4 命中；无误杀 | ⚪ 通过 |

---

## 四、PB 流水线解锁条件进度

| # | 条件 | 状态 |
|---|---|---|
| 1 | Dsharnes-B 提交 F3 两项 P0 回归修复 | ❌ **未提交** |
| 2 | `verify_render ≥ 170/224` + `check_html` 不回退 | ❌ 140/224（`check_html` 169/223 持平） |
| 3 | 本次复审 P0/P1 项二次复审通过 | ❌ 全部未通过 |
| 4 | 替换简版 `pb_pipeline_README.md`(40 行) → 完整版 `PB_PIPELINE_TASK_20260913.md`(181 行) | ❌ **未执行** |
| 5 | 收到明确启动指令 | ⏸️ 无 |

**进度：5/5 全部未满足。PB 流水线继续暂停。**

> 已核对两文件均在场：`pb_pipeline_README.md` 40 行 / `task_queue/to_B/PB_PIPELINE_TASK_20260913.md` 181 行。

---

## 五、待办（优先级不变，全部待 Dsharnes-B 执行）

| 优先级 | 事项 | 动作 | 验收 |
|---|---|---|---|
| **P0** | F3-回归1 | 还原单引号 `window.__tgl('echart_pb_21_c2',this)` | `grep -c '__tgl("' pb_*.html` = 0 |
| **P0** | F3-回归2 | 90 处改 `echart_pb_` 前缀 | `grep -c "getElementById('echart_[0-9]" pb_*.html` = 0 |
| **P0** | 门禁回绿 | 修完重跑 | `verify_render ≥ 170/224` + `check_html` 不回退 |
| **P1** | U4 死代码 | 删除 `EXCHANGE_WHITELIST`（或改造为真正校验） | 引用点 > 1 |
| **P1** | U2 归因 | 补「上期所」中文别名（当前仅 4 处）+ 修正 STATUS.md 归因 | `上期所` 显著增加 |
| **P2** | `check_html` 盲区 | 增补 div-id ↔ `getElementById`/`__tgl` 引用一致性检查 | 本例可静态检出 |

**提交纪律提醒（本次第 2 次前置受阻）**：请 Dsharnes-B 提交修复 commit 后**必须 push 到 `origin/indicator-correction-win`** 并在 `STATUS.md` 写变更记录——`267614d` 已 push，本次无任何新提交可见，复审链路因此再次受阻。

---

## 六、红线声明

- 全程 `git worktree add /tmp/wt_8b513fc 8b513fc` 只读 worktree，审完已 `--force` 清理；`git worktree list` 仅剩 4 个既有项。
- **未修改任何源码**，未污染 main 工作树（`/home/ubuntu/framework-tree` @ `main 404f7ee` 状态未变，仅存在既有 untracked `task_queue/`）。
- 本报告为审计产出，commit 前缀 `[DOC]`。
