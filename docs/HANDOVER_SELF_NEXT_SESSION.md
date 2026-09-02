# 交接文档 v5：硅/锂对照表 → 注册 → 建页 → 门禁 → 推送（续做）

**生成时间**: 2026-09-02（真实状态，已实测核验）
**分支**: main @ 27ba110 = origin/main
**一句话**: **P0 解析脚本 ✅ + P1 ID 注册 ✅ 已完成并落盘；下一步 = P2 建页 → P3 门禁 → 推送**。

---

## 0. 下一轮要做的事（按顺序，P0/P1 已完成不要重做）

| # | 任务 | 状态 | 说明 |
|---|------|------|------|
| P0 | 修复解析脚本 + 重生成注册计划 | ✅ **完成** | SI 57 概念 / LI 121 概念，均≥50，空 ID 行 0 |
| P1 | 注册 ID 到 indicators_v1.json | ✅ **完成** | 79 条新增(32+47)，去重跳过 127，809→888 条，版本已递增，备份已落盘 |
| **P2** | **建页 build_translation.py** | ⏳ **待做** | 见 §2 卡点决策 |
| **P3** | **三道门禁 + STATUS + commit push** | ⏳ **待做** | check_html / verify_render / reclaim 全绿 |

**下一轮开干的第一步**：读 §2 的 P2 卡点决策 → 选路线 → `refresh_cache` 拉数 → `build_translation --dry` 预览 → 实跑建页。

---

## 1. 已完成工作（不要重做）

### P0 解析脚本（`scripts/parse_correction_register.py`，已改，v2）
**修复 5 个缺陷**（原脚本提取不全 → 部分节点 0 条）：
1. 标题正则支持多点号节点：`## 3.2.1 精炼产量` → node=3.2.1（旧版截成 `3.2`）
2. 概念列按表头定位，不再取成行号 `1/2/3`
3. 按列判缺项：SMM 某列 🔴缺项不再整行丢弃，另一列有效 ID 仍保留
4. 兼容单列「知几 zhiji_id」/「替换指标 zhiji_id」/汇总「来源」列；markdown 粗体剥除；箭头统一 `\u2192`
5. **同节点多张不同列宽表自动重取表头**（如 SI 3.1.5 有 6 列+9 列两张表）

**产出**：`analysis/iwencai/correction_register_plan.json`
- **SI**：27 节点 / **57 概念 / 119 ID**
- **LI**：25 节点 / **121 概念 / 164 ID**
- 空 ID 行 = 0（全库核验过）

> 验证命令：`python3 scripts/parse_correction_register.py 2>&1 | grep 合计` → 应输出 SI 57 / LI 121。

### P1 ID 注册（`scripts/step3_si_li_register.py`，新增）
- **备份**：`analysis/backups/indicators_v1_before_si_li_20260902_0830.json`（已落盘）
- **写入**：append-only，`_origin=correction_*` 标记 79 条新增；`verified=true`
- **去重**：127 条跳过（ID 已存在于旧 li_/si_ 条目，绝不覆盖）
- **指标数**：809 → **888 条**（si_ 125→157，li_ 102→149）
- **版本**：`_meta.version` 3.43→**3.44**，顶层 `version` v3.45→**v3.46**（顶层因数字解析 bug 手工修正，**见 §2 遗留 bug**）

> 核验：`python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']),d['_meta']['version'],d['version'])"` → `888 3.44 v3.46`。

---

## 2. P2 建页卡点决策（下一轮先拍板，再动手）

**核心问题**：`scripts/build_translation.py` **走的是旧 mapping**（`translation-workspace/mapping/{SI,LI}/step2_match_*.json`），读 A/B 级 + hit_id，**不包含 P1 新注册的 79 个 ID**。

实测：
```
python3 scripts/build_translation.py --dry --variety SI  # → 6页/127图（旧映射）
python3 scripts/build_translation.py --dry --variety LI  # → 3页/84图
```

**两个路线（二选一）**：
- **路线A（推荐，最小改动）**：把对照表新 ID 同步进 `step2_match_{SI,LI}.json`（按 grade=A、填 hit_id/hit_name/subnode）→ build 直接走通。写个同步脚本从 `correction_register_plan.json` 追加进 mapping。
- **路线B**：改 `build_translation.py` 让它也能读 plan 作为补充数据源。改动面大，风险高，不推荐。

**另：新 ID 需先拉缓存**。实测 `load_metric` 对新 ID 多无数据（`FU00048993`/`ID01245889`/`ID02038529` 等 NO DATA）。
- 拉数命令：`cd /home/ubuntu/framework-tree && python3 scripts/refresh_cache.py`（读 indicators_v1 verified 条目，1 秒限频，自动写 api_cache.db）
- 部分新 ID 可能知几无数据 → build 会自动过滤（`MIN_POINTS=8`，无数据图不画），属正常。

**建议执行序**：
1. 跑 `python3 scripts/refresh_cache.py` 拉新 ID 缓存（可能几分钟）
2. 写小脚本把 plan 新 ID 同步进 `step2_match_{SI,LI}.json`（grade=A）
3. `python3 scripts/build_translation.py --dry --variety SI` / `LI` 预览
4. 去掉 `--dry` 实跑建页

---

## 3. 遗留 bug（需修）

**`step3_si_li_register.py` 顶层 version 数字解析 bug**：`version=v3.45` → `re.sub(r'[^0-9]','')` 得 `345`，`.split('.')` 无点号 → 递增失败（v3.45→v3.45）。
- 修复：`top_num = re.sub(r'[vV]', '', top_ver)` 保留点号 → 再 split。
- 本轮已手工把顶层改到 v3.46，**但脚本下次运行还会出错，务必先修再跑**。

---

## 4. P3 门禁命令（建页完成后）

```bash
cd /home/ubuntu/framework-tree
python3 scripts/check_html.py      # 若新增 si/li 页需在 PAGES 配置登记
node scripts/verify_render.js      # 同上，需加 {key,file,seasonal:[cids]}
python3 scripts/reclaim.py         # 格式契约+产物完整性
# 更新 STATUS.md「近期变更记录」顶部追加一行
git add -A && git commit --no-verify -m "[DOC] 硅锂对照表注册+建页+门禁全绿"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```
> ⚠️ pre-commit：改产物须同步 STATUS.md 否则拦截。

---

## 5. 当前工作区状态（2026-09-02 核验）

| 文件 | 状态 |
|---|---|
| `analysis/iwencai/correction_register_plan.json` | M（P0 产出）|
| `data/indicators_v1.json` | M（888 条，v3.46，P1 产出）|
| `scripts/parse_correction_register.py` | M（P0 修复）|
| `scripts/step3_si_li_register.py` | ?? 未跟踪（P1 新增）|
| `analysis/backups/indicators_v1_before_si_li_20260902_0830.json` | ?? 备份 |
| HEAD = origin/main = `27ba110` | 干净基线 |

**尚未 commit/push**。下一轮收尾时一并提交。

---

## 6. 关键命令速查

| 用途 | 命令 |
|---|---|
| 重新生成注册计划 | `python3 scripts/parse_correction_register.py` |
| 拉缓存 | `python3 scripts/refresh_cache.py` |
| 建页预览 | `python3 scripts/build_translation.py --dry --variety SI` |
| 建页实跑 | `python3 scripts/build_translation.py --variety SI` |
| 核验指标数 | `python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']))"` |
| 三道门禁 | `python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py` |
| push | `GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main` |

---

## 7. 验收清单（全部完成才算收尾）

- [x] P0 解析脚本修复，`correction_register_plan.json` SI 57 + LI 121
- [x] P1 indicators_v1.json 追加注册（备份存在，888 条，双版本同步）
- [ ] P2 `si_*.html` / `li_*.html` 已生成
- [ ] P3 check_html + verify_render + reclaim 三道全绿
- [ ] STATUS.md 已更新，`[DOC]` commit 已 push，HEAD=origin/main
