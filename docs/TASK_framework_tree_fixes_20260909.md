# framework-tree 修复任务卡 · 2026-09-09

> **给**：本地 agent（Windows，有写权限）
> **来源**：飞书主脑诊断（无写权限，只出方案）
> **分支**：`git checkout -b task/li314_fix` 基于最新 main（HEAD=05db1d2）

---

## 0. 开工前基线（强制，见 AGENTS.md）

```bash
cd ~/framework-tree   # Windows: D:\DSH_WORK\framework-tree
git fetch origin && git rebase origin/main
git checkout -b task/li314_fix
bash scripts/bootstrap_agent.sh   # 6项检查全绿才开工
python3 ~/.hermes/scripts/file_write_lock.py acquire <dir> agent:local
```

---

## 1. 任务清单（按优先级）

### P0: 修复 li_3_1_4 指标串台（明确 bug，1个页面）

**根因**：tree_config 3.1.4 定义 = "矿进口量与分国别"，但 li_3_1_4.html 挂的是 `li_314_inv`（碳酸锂库存）。

| 项 | 值 |
|---|---|
| 错指标 | `li_314_inv` 碳酸锂库存中国（月）|
| 正确正主 | `li_32_by_country_import_conc` 锂精矿进口分国别（月频，吨，verified=True）|
| 备选正主 | `li_61_by_country_import_conc`（周频，万吨，含澳洲/南美/智利/非洲）|
| 参考 | 其他品种 3.1.4 都是矿进口：cu_3_1_4=铜矿进口、zn_3_1_4=锌矿进口、sn_3_1_4=锡矿进口 |

**步骤**：
1. 读 `scripts/build_li_3_1_4.py`（或对应 build 脚本），把指标 ID 从 `li_314_inv` 改为 `li_32_by_country_import_conc`
2. 同步改 `data/indicators_v1.json` 里 li_3_1_4 节点引用的指标（如果有引用）
3. 改图标题/副标题/图备注为"锂精矿进口分国别"
4. 重建页面 `python3 scripts/build_li_3_1_4.py`
5. 跑三道门禁

### P1: 周报图接入 index.html PAGE_MAP（24张页面不可导航）

**根因**：24 张周报图（7 AO + 17 wr）文件在 main 里，但 index.html 的 PAGE_MAP 没有它们的 key，看板看不到。fallback 逻辑（L397）只覆盖 ZN/NI/SN/SI/LI/LC 6 个品种，不含 AO，也不认 `wr` 后缀文件名。

**步骤**：
1. 读 `index.html` L288-L397（PAGE_MAP + fallback）
2. 给 24 张周报图加静态 PAGE_MAP key（例：`li_3_2_1wr: 'li_321wr_production.html'`）
3. AO 品种加进 fallback 列表，或为 7 张 AO 周报图加静态 key
4. `wr` 后缀文件名处理：fallback 派生逻辑要能识别 `li_321wr_production` → 不走 fallback，走静态 key
5. 跑 `node scripts/verify_render.js` 确认新页面可渲染

**24 张周报图清单**：
- AO 7：ao_2_2, ao_2_3, ao_3_1_3, ao_3_1_4, ao_3_2_1, ao_4_2, ao_4_4, ao_7_1
- LI 6：li_3_1_3, li_3_2_1, li_3_2_2, li_4_1, li_6_1, li_7_1（wr 后缀版）
- NI 5：ni_2_3, ni_2_4, ni_4_1, ni_4_3, ni_6_1
- SI 3：si_2_3, si_3_2_1, si_7_1
- AL 2：al_2_3, al_4_1
- SN 1：sn_2_3

### P2: 指标去重（每个指标只出现在一个图）

**目标**：用户要求"每个指标只出现在一个图里，别太重复"。

**步骤**：
1. 写脚本扫描所有 build_*.py，统计每个指标 ID 出现在哪些页面的哪些图里
2. 找重复指标（同一 ID 在 2+ 图）
3. 按"正主优先"原则保留：正主节点的图保留，辅助图删除或替换为辅助指标
4. 参考 AGENTS.md 第3.5节"指标取舍5规则"——正主防串用规则

### P3: 系统性指标错配筛查（主脑已跑一遍，见下方诊断报告）

主脑已跑系统性筛查（结果见 `/home/ubuntu/output/指标错配筛查报告_20260909.md`），发现 li_3_1_4 是明确的串台。本地 agent 需复核并修复报告中列出的其他错配项。

---

## 2. 门禁（三道全绿才提交）

```bash
python3 scripts/check_html.py       # 期望全过
node scripts/verify_render.js        # 期望全过
python3 scripts/reclaim.py           # 期望 PASS
```

---

## 3. 提交

```bash
# pre-commit hook 强制改产物必须动 STATUS.md
# 改完 HTML/JSON 后必须更新 STATUS.md 近期变更记录
git add -A
git commit -m "[FIX] li_3_1_4指标串台修复+周报图接入PAGE_MAP+指标去重"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin task/li314_fix
```

然后开 PR 或让主脑 merge。

---

## 4. 数据源注意

- **SMM 锁定**：a1/j0/s2 前缀指标 code=10017，182 条拉不到（zhiji 后端问题，非本地）
- **知几 FU/ID/CM00 前缀可用**：继续用
- 新建页只能用 verified=True 的指标（见 indicators_v1.json）
