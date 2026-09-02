# 交接文档 v8：合并 Windows Agent 成果 + 锂硅指标修复 + 主页全覆盖（2026-09-02 新会话续）

**生成时间**：2026-09-02（主脑实测版，非沿用旧文档）
**仓库**：`/home/ubuntu/framework-tree`（GitHub: algo23-yunqingtian/framework-tree）
**上一版交接**：`docs/HANDOVER_AGENT_20260902_2.md`（v7，部分结论已过时，见 §3）

---

## 0. 一句话状态

**7 金属 correction 全做完（锂硅铅在 main、铜铝镍锡在 win 分支），但 win 分支 110 条指标注册卡在分支没合并，锂硅指标库是空壳（verified=False），主页 7 个品种总页全缺失。** 下一步 = 合并 win 分支 → 锂硅补注册 → 建品种总页 → 统一命名 → 推 Pages。

---

## 1. 当前实测基线（2026-09-02 主脑核验）

| 指标 | 实测值 |
|---|---|
| origin/main HEAD | `e195b57`（[DOC-v7] 交接文档） |
| 本地 HEAD | `e195b57`（与 origin/main 同步） |
| indicators_v1.json | **888 条 / v3.46**（main 线，锂硅大量 verified=False） |
| PAGE_MAP 总条目 | 94（AL25/CU25/LC14/PB30） |
| 主页 5M fallback | ✅ 存在（ZN/NI/SN/SI/LI 动态推导 `{code}_N_N.html`） |
| 品种总页（li.html/pb.html 等 7 个） | ❌ 全部不存在 |
| 远端 Pages 首页 | 与本地 index.html 字节一致（26182B）= 已是最新 |
| GitHub Pages 入口 | `https://algo23-yunqingtian.github.io/framework-tree/` |

### worktree / 分支清单

| worktree | 分支 | 状态 |
|---|---|---|
| `/framework-tree` | main `e195b57` | 干净（3 个 HANDOVER_SUPERVISOR*.md 未跟踪） |
| `/framework-tree-cu` | task/cu_price `4512520` | 干净，领先 main 5 commit（铝2.x/铜铝建页） |
| `/framework-tree-export` | feature/export-module `a4a8bd0` | 干净，领先 main 5 commit（71页串节点修复+NI重建） |
| `/tmp/wt_cu` | detached `4512520` | — |
| 远端分支 | `origin/indicator-correction-win` | **领先 main 8 commit（Windows Agent）** |

**注意**：main 工作区有 3 个未跟踪文件 `docs/HANDOVER_SUPERVISOR_*.md`，勿动。

---

## 2. Windows Agent 做了什么（origin/indicator-correction-win，Author=CU-Agent）

**9/2 全天 8 commits，覆盖 CU/AL/NI/SN 4 金属，110+ 指标注册到 v3.48**：

| commit | 时间 | 内容 |
|---|---|---|
| e1fd99d | 09-02 00:54 | 铜供给 3.1-3.6 共 35 指标知几验证（A=25 B=5 C=6） |
| df5bf79 | 09-02 07:11 | 同花顺纠正第一轮：CU+AL+NI+SN **22 份对照表** |
| cc70b6c | 09-02 07:11 | 交接文档 v2：22 板块完成清单+并行策略 |
| c69ba97 | 09-02 07:27 | 铜库存 4.1-4.5 共 23 指标验证（A=14 B=3 C=6）+ HANDOVER |
| fb37e29 | 09-02 08:45 | 全量补搜：AL/NI/SN 全部 15 个对照表 |
| 2ad8ed6 | 09-02 11:23 | CU/AL/NI/SN correction 质量修正+目录重构 + **P1 注册 110 指标** |
| 514af81 | 09-02 12:28 | P1 v2：7 个 AL 指标 + AL价格(7A)/AL需求(15A)/CU需求(3A)/CU成本利润(2A) |
| f73bccb | 09-02 12:59 | P1 v3：CU价格v4(9A)+SN成本利润v3(5A)+CU供给fix(21A)+注册4指标 → **v3.48** |

**产物**：158 个 translation-workspace 文件 + `data/indicators_v1.json`（改到 v3.48）。
**zhiji 搜索记录**：31 份 `*_zhiji_search.json`（AL6/CU8/NI6/SN6/混合5），证明按同花顺全称逐个搜了 zhiji。
**没做的**：LI/SI/PB 3 金属（在 main 线）、建页渲染、主页/PAGE_MAP、品种总页。

### win 分支文件目录结构

```
translation-workspace/correction/
├── CU/  (价格/供给/库存/需求/进出口/成本利润 6 板块)
├── AL/  (同 6 板块)
├── NI/  (同 6 板块)
├── SN/  (同 6 板块)
├── cu-al-ni-sn/ (混合产物 67 文件)
├── ZN_*_correction_20260901.md (锌，旧)
└── LI/ SI/ PB/ (这些在 main 分支，win 没有)
```

---

## 3. main 线（主脑）做了什么（与 win 互补）

| 金属 | 状态 |
|---|---|
| **LI 锂** | ✅ 12 份 correction/r1 已 push main（价格/供给/库存/需求/进出口/成本利润） |
| **SI 硅** | ✅ 13 份已 push main（供给拆矿端/冶炼端） |
| **PB 铅** | ✅ 7 份已 push main（9/1-9/2） |
| **ZN 锌** | ✅ 6 份已 push main（9/1） |
| **硅锂建页** | ⚠️ 12 页 274 图已建（commit a00c63e），但**指标库空壳** |

### 锂硅指标库空壳问题（核心卡点）

- 指标库 LI 覆盖 126 条、**LC 仅 6 条**，大量 `verified=False`
- correction 里已判明正确 ID（如 `a12808678` 澳锂辉石精矿）**只存在于 .md，没注册进 indicators_v1.json**
- `li_3_1_5.html` 只有 3 张图、标题"3.1.5 3.1.5"重复 = 空壳页
- 根因：correction（图纸）→ 注册 → 建页 链路后半段没跑完

### 已过时结论（v7 交接文档 vs 实测）

| v7 声称 | 实测 | 判定 |
|---|---|---|
| "ZN/NI/SN/SI 完全不能 chip 跳转" | 有 5M fallback 动态推导，本来就不需进 PAGE_MAP | ❌ v7 结论不准 |
| HEAD=d89a431 | 实际 e195b57（v7 自身已入 main） | ⚠️ |
| Pages 旧 | 本地=远端字节一致，已最新 | ❌ 不是 git 问题，是 UI 缺入口 |

---

## 4. 待办清单（新会话按序执行）

### P0 🔴 合并 win 分支（110 条注册成果上线）
```bash
cd /home/ubuntu/framework-tree
python3 ~/.hermes/scripts/file_write_lock.py acquire /home/ubuntu/framework-tree agent:merge-win
# 备份 indicators_v1.json → data/backups/indicators_v1_<日期>.json
git merge origin/indicator-correction-win   # 可能冲突：ZN correction 与 main v1 撞车
# 门禁三连：python3 scripts/check_html.py / node scripts/verify_render.js / python3 scripts/reclaim.py
python3 ~/.hermes/scripts/file_write_lock.py release /home/ubuntu/framework-tree
```

### P1 🔴 锂硅指标补注册（correction → indicators_v1.json）
- 按 LI/SI 共 25 份 correction 的 ✅ 真实 ID（如 a12808678）批量注册
- 把 verified=False 占位替换为真实 ID
- LI 至少补到 ~120+ 条 verified=True，LC 主键覆盖

### P2 🟡 重建硅锂问题页
- `li_3_1_5.html` 等 3 页用新注册 ID 重建，标题去重

### P3 🟡 建 7 个品种总页 + 统一命名
- 建 li.html/cu.html/al.html/zn.html/ni.html/sn.html/si.html/pb.html 品种首页（三层导航：品种→板块→叶子）
- 命名统一：PB 旧名（pb_71_cost_curve.html）→ 新名（pb_7_1.html）
- overview 页**不挂 chip**，保持 chip=叶子语义

### P4 🟢 锌镍锡硅 4 品种指标错配核对（同花顺复核）
- win 分支已做 CU/AL/NI/SN correction，ZN 需对照 win 产物交叉检查
- SI 多晶硅下游交叉验证（需求节点辅助指标）

### 上线
- git push + Pages 重建（Pages 有限频，push 后等重建）
- 用户浏览器强刷（Cmd+Shift+R）

---

## 5. 关键决策点（用户已给方向）

1. **命名体系**：统一用新 `{code}_N_N.html`（如 `zn_3_1_1.html`），反向修 PB 旧名 ✅ 已定
2. **overview 入 chip**：不挂，chip=叶子 ✅ 已定
3. **锂矿 TC**：correction 判为概念幻觉（Trina 定价无 TC 体系），需同花顺再复核是否有不叫 TC 的"锂精矿加工费"真实序列 ⏳ 待复核
4. **工业硅 vs 多晶硅**：可带多晶硅作下游需求交叉验证，标"辅助"不喧宾夺主 ✅ 已定

---

## 6. 关键文件路径

| 用途 | 路径 |
|---|---|
| 本交接文档 | `/home/ubuntu/framework-tree/docs/HANDOVER_AGENT_20260902_3.md` |
| 上一版交接(v7) | `/home/ubuntu/framework-tree/docs/HANDOVER_AGENT_20260902_2.md` |
| 主页 HTML(含PAGE_MAP) | `/home/ubuntu/framework-tree/index.html` |
| 指标库 | `/home/ubuntu/framework-tree/data/indicators_v1.json`（888/v3.46） |
| 目录树配置 | `/home/ubuntu/framework-tree/data/tree_config.json` |
| 全局状态 | `/home/ubuntu/framework-tree/STATUS.md` |
| 锂校正 | `translation-workspace/correction/LI/LI_供给_correction_20260902.md` |
| 硅校正 | `translation-workspace/correction/SI/SI_供给冶炼端_correction_20260902.md` |
| win 分支产物 | `origin/indicator-correction-win`（CU/AL/NI/SN 158 文件） |
| 双agent协作协议 | `/home/ubuntu/framework-tree-cu/docs/AGENT_PARALLEL_PROTOCOL.md` |
| 文件锁脚本 | `~/.hermes/scripts/file_write_lock.py` |

---

## 7. 开工前基线核验（强制）

```bash
cd /home/ubuntu/framework-tree && git fetch origin && git log --oneline -3 origin/main
# 必须 ≥ e195b57；若出现 win merge commit 说明已合并过
git merge-base origin/main origin/indicator-correction-win   # 查分叉点防冲突
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print(len(d['indicators']), d['version'])"
# 必须 888 / v3.46（merge 后应 v3.48+）
git worktree list && git status -s   # 确认无人在写
```

---

**一句话**：win 分支（铜铝镍锡 110 指标 v3.48）和 main（锂硅铅锌 correction + 硅锂 12 页）合起来才是完整 7 金属。新会话第一步 = merge win 分支过三道门禁 → 锂硅补注册 → 建品种总页 → 统一命名 → 推 Pages。
