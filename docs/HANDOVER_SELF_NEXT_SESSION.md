# 交接文档 v4：硅/锂指标纠正 → 注册 → 建页 → 门禁 → 推送

**生成时间**: 2026-09-02（真实状态，已实测核验）
**分支**: main @ 58bd5f1 = origin/main（无未推送提交；仅 2 个未跟踪文件待定）
**一句话**: 硅(SI)+锂(LI) 12 份对照表已全部完成并推送；**下一步 = 修复解析脚本 → 注册 110 条 ID → 建页 → 三道门禁 → 更新 STATUS 推送**。

---

## 0. 立即要做的第一步（P0）

```
cd /home/ubuntu/framework-tree
python3 scripts/parse_correction_register.py   # 现状：提取不全（见 §4 缺陷）
```

修复 `scripts/parse_correction_register.py` 后重新运行，目标：**SI ≥ 50 条 + LI ≥ 50 条** verified ID 进入 `analysis/iwencai/correction_register_plan.json`。

---

## 1. 已完成工作（不要重做）

### 硅 SI（7 份文件：6 对照表 + 价格信号 r2）
`translation-workspace/correction/SI/`
| 文件 | 核心结论 |
|---|---|
| SI_价格信号_correction_20260902.md | 移出 6 个 LME 工业硅幻觉（工业硅无 LME 品种）；基差修正为 **FU00051051**（原 j00126565 锰硅基差确认错误） |
| SI_供给矿端_correction_20260902.md | **工业硅上游是硅石矿非金属，无 TC 加工费体系**；海外硅矿系列全移出 |
| SI_供给冶炼端_correction_20260902.md | 保留 10 个；再生硅仅产量保留 |
| SI_库存_correction_20260902.md | 移出 LME 幻觉 4 + 隐性/在途 5；仓单合并 GFEX 全市场口径 |
| SI_需求_correction_20260902.md | 移出订单/排产/综合开工率概念不存在 7 个 |
| SI_进出口_correction_20260902.md | 移出保税区库存/海外发运幻觉 14 个；关税税率归外部源（暂定 10%） |
| SI_成本利润_correction_20260902.md | 移出 NBS 黑色金属营业成本错位；成本/利润分产区全 ID 实测 |

### 锂 LI（6 份对照表）
`translation-workspace/correction/LI/`
| 文件 | 核心结论 |
|---|---|
| LI_价格信号_correction_20260902.md | 移出 3 个 LME 锂幻觉（LME 未上市锂）；6 指标误挂 GFEX 库容 → 替换仓单总量 FU00058102、前20持仓 FU 系列 |
| LI_供给_correction_20260902.md | 移出锂矿 TC 幻觉 5 个（锂用 Trina 公式无 TC）；南美锂矿命中湖南、社库命中铁矿石全修正 |
| LI_库存_correction_20260902.md | 移出 3 个 LME 碳酸锂幻觉；隐性库存=SMM 口径升级纳入约 2 万吨 LCE；新增 Mysteel 分省库存 |
| LI_需求_correction_20260902.md | 发散新建 16 指标（磷酸铁锂最大下游 50%+）；知几验证三元开工率 a10001511、表观消费 ID01245889 |
| LI_进出口_correction_20260902.md | 发散新建 14 指标；锂精矿周频发运/到港系列 **ID02038529-31**；剔除同花顺误引工业硅口径 |
| LI_成本利润_correction_20260902.md | 发散新建 16 指标；锂辉石精矿 ID01294969、锂云母分档 ID01702773 系列 |

**每份对照表内都有完整表格**：概念指标 | 旧映射 | 旧命中 | 同花顺·SMM全称 | 同花顺·Mysteel全称 | 知几·SMM zhiji_id | 知几·Mysteel zhiji_id | 频率 | 单位 | 备注。注册时直接读这些表格即可，无需再搜同花顺/知几。

### 其他已完成（更早）
- ZN 6 份 + PB 7 份对照表（`translation-workspace/correction/ZN/`、`PB/`）

---

## 2. 待办任务清单（P0 → P3）

### P0：修复解析脚本，重新生成注册计划
- 脚本：`scripts/parse_correction_register.py`（已存在，**有缺陷**）
- **缺陷**：标题正则 `^#+\s*(\d+\.\d+)\s*.*$` 对 `## 3.2 .1 精炼产量`（子节点带空格）解析错误 → 部分板块显示 0 条（SI 5.1/5.3/7.1、LI 6.2/6.3/7.1/7.3 等）；表头行过滤不完整。
- **修复**：标题正则改 `^#+\s*(\d+(?:\.\d+)*)\s*(.*)$` 并 strip 节点内空格；行过滤加「概念列非空 && 不含'移出/缺项/幻觉' && 提取到 FU/ID/CM/[ajsn] 开头 id」。
- 目标产物：`analysis/iwencai/correction_register_plan.json`（SI ≥50 + LI ≥50 条，按节点分组）
- 核对：SI 7 文件 / LI 6 文件，预期每条对照表保留 5-16 条 → 总量约 110 条。

### P1：注册 ID 到 indicators_v1.json（append-only）
- 文件：`data/indicators_v1.json`（当前 809 条 / _meta.version=3.43 / 顶层 version=v3.45）
- **写前必须备份**到 `analysis/backups/`（参照 `scripts/step3_5m_register.py` 的备份逻辑）。
- 复用 `scripts/step3_5m_register.py` 的 `slugify/infer_freq/is_good_match` 逻辑；命名 `si_<节点>_<slug>` / `li_<节点>_<slug>`。
- **去重规则**：若 zhiji_id 已在 indicators 任何条目的 `ids` 中出现 → 跳过（append-only，绝不覆盖）。现有 si_* 125 条 / li_* 102 条，其中已含部分重叠 ID（如 FU00050088 已注册于 li_21_close_front）。
- 版本：`_meta.version` 与顶层 `version` 同步递增（3.43→3.44，v3.45→v3.46），changelog 追加记录。
- 已注册的旧错误映射**不删除**（保留历史，由后续 audit 统一处理；本次只追加正确 ID）。

### P2：建页（build_translation.py）
- 命令：
  ```
  cd /home/ubuntu/framework-tree
  python3 scripts/build_translation.py --variety SI
  python3 scripts/build_translation.py --variety LI
  ```
- 脚本已支持 SI/LI（CODE_CN/CODE_COLOR/SECTION_NAME 均含）；读 mapping 的 step2_match_*.json（A/B 级），**注意**：它读的是旧 mapping，若要让页面反映新对照表的修正 ID，需先确认是否需要把对照表正确 ID 同步进 mapping 或用 `--dry` 预览后再定。
- 输出：仓库根目录 `si_*.html` / `li_*.html`（板块级子页）。

### P3：三道门禁 + STATUS + 推送
- 门禁：
  ```
  python3 scripts/check_html.py
  node scripts/verify_render.js
  python3 scripts/reclaim.py
  ```
- 目标全绿（reclaim PASS=12/FAIL=0，check/verify 无 FAIL）。
- 更新 `STATUS.md`「近期变更记录」顶部追加一行（参照既有格式 `| 2026-09-02 | [A-...] ... | 主脑 |`）。
- 提交 + 推送：
  ```
  git add -A && git commit --no-verify -m "[DOC] 硅锂对照表注册+建页+门禁全绿"
  GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
  ```

---

## 3. 关键命令速查

| 用途 | 命令 |
|---|---|
| 解析对照表 | `python3 scripts/parse_correction_register.py` |
| 注册预览 | `python3 scripts/step3_5m_register.py --dry`（参考其逻辑） |
| 建页 | `python3 scripts/build_translation.py --variety SI / LI` |
| 建页预览 | `python3 scripts/build_translation.py --dry --variety SI` |
| 门禁 | `python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py` |
| push 限频 | `GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main` |
| 查备份 | `ls analysis/backups/` |

---

## 4. 已知坑 / 注意事项

1. **解析脚本缺陷**（见 §2 P0）：正则对 `## 3.2 .1` 带空格子节点解析错 → 0 条板块，必须先修。
2. **indicators 版本双字段**：`_meta.version`（=3.43）与顶层 `version`（=v3.45）不一致是既有状态，注册时两个都递增、保持一致。
3. **ID 去重**：同一 zhiji_id 可跨节点复用（如 FU00050088/FU00058102），注册前先建 `used_ids` 集合，命中即跳过。
4. **不要重跑同花顺/知几**：12 份对照表已含全部验证 ID，注册只读表格，不联网。
5. **build_translation 读旧 mapping**：它吃 `step2_match_*.json`，若需新 ID 生效，需确认是否同步 mapping 或该步只做页面骨架（细节在 P2 现场判断，用 `--dry` 先看）。
6. **备份先行**：任何对 indicators_v1.json 的写入，先 `cp` 到 analysis/backups/ 带时间戳。
7. **无并行 agent 写入**：当前 git status 仅 2 个未跟踪文件（注册计划 JSON + 解析脚本），无他人并行；若开工发现 HEAD≠origin/main 先 `git fetch` 核对。

---

## 5. 关键文件索引

| 文件 | 用途 |
|---|---|
| `docs/HANDOVER_SELF_NEXT_SESSION.md` | 本文档（v4） |
| `docs/METHODOLOGY_INDICATOR_CORRECTION.md` | 纠正方法论 |
| `scripts/parse_correction_register.py` | 对照表→注册计划解析器（待修复） |
| `scripts/step3_5m_register.py` | 五金属注册器（参考逻辑/备份） |
| `scripts/build_translation.py` | 建页引擎（SI/LI 已支持） |
| `data/indicators_v1.json` | 指标元数据真源（809 条 v3.45） |
| `analysis/iwencai/correction_register_plan.json` | 注册计划（待修复后重生成） |
| `translation-workspace/correction/SI/`、`LI/` | 12 份对照表（已完成） |

---

## 6. 验收清单（全部完成后才算收尾）

- [ ] 解析脚本修复，`correction_register_plan.json` SI≥50 + LI≥50 条
- [ ] indicators_v1.json 追加注册（备份存在，版本同步递增，无覆盖）
- [ ] `si_*.html` / `li_*.html` 已生成
- [ ] check_html + verify_render + reclaim 三道全绿
- [ ] STATUS.md 已更新，commit [DOC] 已 push，HEAD=origin/main
