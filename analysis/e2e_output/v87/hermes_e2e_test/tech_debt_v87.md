# V87-RC1-G1 技术债台账

> **版本**: V87-RC1-G1
> **编制日期**: 2026-10-12
> **编制方**: HERMES Agent (Phase18)
> **文档版本**: v1.0
> **处理原则**: Release阶段不修复，标记下一版本迭代处理

---

## 0. 摘要

| 项 | 值 |
|---|---|
| 技术债总数 | **3 项** |
| 阻断级（P0/P1） | **0** |
| 低优先级（P3/记录级） | **3** |
| Release阶段处置 | **全部标记"Release阶段不修复"** |
| 后续版本 | V88-RC1 或下一迭代处理 |

**核心原则**: 本台账记录的技术债均为**非阻断性历史遗留问题**，不影响 V87-RC1-G1 的 Release Gate 评审（GO 14/14 + 三方共识 GO + 0 P0/P1/P2）。全部标记为"下一版本迭代处理"，在 Release 评审中作为已知限制项纳入风险观测清单。

---

## 1. 技术债清单

### TD-V87-001: MD5_MANIFEST_cross_review.md 历史UTF-8编码损坏

| 项 | 内容 |
|---|---|
| **编号** | TD-V87-001 |
| **等级** | P3（低） |
| **引入阶段** | Phase01（历史遗留） |
| **影响范围** | `analysis/e2e_output/v87/hermes_e2e_test/MD5_MANIFEST_cross_review.md` |
| **描述** | 文件首行 `# MD5_MANIFEST V87-RC1 总清单` 处的 `V` 字符为非法 UTF-8 字节 `0x3F`（`？` 的 UTF-8 编码被截断）。文件混合 CRLF（\r\n）、LF（\n）、NEL（\x85）三种行终止符。`file` 命令报告为 `Non-ISO extended-ASCII text, with very long lines (392), with CRLF, LF, NEL line terminators`。 |
| **根因** | Phase01 初始创建文件时编辑器/工具链编码不一致，后续追加内容均在此基础上追加，导致坏字节被继承 |
| **影响** | (1) Python `open(path, encoding="utf-8")` 在首行抛 `UnicodeDecodeError`，需用 `errors="replace"` 或字节级操作；(2) 部分文本搜索/正则工具可能误报或遗漏首行内容；(3) 不影响 KV 对解析（键值对均为纯 ASCII） |
| **当前处置** | **Phase17 PREP 工单**中因 rebase 冲突需操作此文件，采用**字节级方式**（`open(path, "rb")`）处理冲突标记，**未修改历史坏字节**，仅追加新内容 |
| **Release阶段处置** | **不修复**。修复需重新编码整个文件（约 1911 行），会导致 MD5 校验链断裂（Phase01~17 所有 MD5 清单段的哈希值变化），影响范围过大 |
| **下一版本处置** | V88-RC1 中将文件整体重编码为 UTF-8 + 统一行终止符 LF，同步更新所有引用此文件 MD5 的元数据文件 |
| **验证方式** | `file MD5_MANIFEST_cross_review.md` 报告 `Non-ISO extended-ASCII text` |

### TD-V87-002: reclaim FAIL=4（Phase03~15 历史契约缺失）

| 项 | 内容 |
|---|---|
| **编号** | TD-V87-002 |
| **等级** | P3（低） |
| **引入阶段** | Phase03~Phase15（历史遗留） |
| **影响范围** | `STATUS.md` 历史 Phase03~15 段落 |
| **描述** | `scripts/reclaim.py` 报告 `PASS=9 FAIL=4`，4 项 FAIL 均为：(1) 缺「B→A 待办」区、(2) 缺「A→B 待办」区——均为 `STATUS.md` 历史 Phase03~15 段落中线 A 表格契约缺失 |
| **根因** | 早期 Phase 的 STATUS.md 段落未严格遵循 `docs/COLLABORATION_PLAYBOOK.md` 第 3 章定义的表格契约格式（缺线 A 标记、缺待办分区） |
| **影响** | reclaim 的 4 项 FAIL 不影响 check_html 门禁（266/266 PASS），不影响审计交付物有效性，不影响 JOB_READY.flag 标记 |
| **当前处置** | Phase16 记录、Phase17 如实报告不修、Phase18 本台账正式登记。**全部处置均为"仅记录不修改历史文件"** |
| **Release阶段处置** | **不修复**。修复需修改 Phase03~15 的 STATUS.md 历史段落，破坏历史段落格式一致性，超出审计交接类工单范围 |
| **下一版本处置** | V88-RC1 中作为独立工单处理，修改历史段落时保持格式一致性，并在修改时同步更新 reclaim 基线 |
| **验证方式** | `python3 scripts/reclaim.py` 输出 `汇总: PASS=9 FAIL=4` |

### TD-V87-003: 金丝雀仿真放大基线的方法学局限

| 项 | 内容 |
|---|---|
| **编号** | TD-V87-003 |
| **等级** | P3（低，方法学限制） |
| **引入阶段** | Phase17（金丝雀审计） |
| **影响范围** | `phase17_canary/canary_audit.py` + `phase17_canary_results.json` |
| **描述** | Phase17 金丝雀审计因 DSHE Phase30 工单尚在运行、无真实金丝雀时序数据可用，采用 Phase16 的 60 天混合窗口（180 行）按 30 秒粒度 × 6 因子采样放大至 6480 点等效量级。双版本 100% 一致结论建立在同一窗口数据上，等价于"无版本差异输入 → 无版本差异输出"的逻辑自洽性验证，而非独立真实分流验证。 |
| **根因** | 金丝雀工单（DSHE Phase30）与审计工单（HERMES Phase17）并行执行，时序上无法等待真实金丝雀数据 |
| **影响** | (1) Phase17 金丝雀基线（100 处隐性差异）为仿真分布，非生产真实观测；(2) 双版本 100% 一致是逻辑自洽性而非独立验证；(3) 可能在后续引用中被误当生产真实观测值 |
| **当前处置** | **Phase18 T1** 已用 DSHB Phase30 真实金丝雀数据（18,720 比对点 / 72h / 26 因子 / 10 维度）替换仿真基线，完整对比报告见 `v87_rc1_hermes_p18_canary_real_traffic_obs_report.md` |
| **Release阶段处置** | **不修复 Phase17 产物**（NO_OVERWRITE 约束）。Phase17 报告已在对应章节标注"仿真放大"字样 |
| **下一版本处置** | V88-RC1 的金丝雀审计直接使用真实生产金丝雀流量，不再依赖采样放大方法学 |
| **验证方式** | Phase17 `phase17_canary_results.json` 的 `canary_rows=636` + `staging_rows=5844`（总 6480）vs Phase30 真实 18,720 点 |

---

## 2. 技术债与 Release Gate 的关系

| 技术债 | Gate 影响 | Release 评审态度 |
|---|---|---|
| TD-V87-001 编码损坏 | ❌ 无影响（不影响 KV 解析、不影响 check_html） | 已知限制，不阻断 Release |
| TD-V87-002 reclaim FAIL=4 | ❌ 无影响（check_html 266/266 PASS） | 已知限制，不阻断 Release |
| TD-V87-003 仿真放大 | ❌ 无影响（Phase18 已用真实数据替换验证） | 已知限制，Phase18 已做真实复测 |

**结论**: 3 项技术债均为**非阻断性历史遗留**，不影响 V87-RC1-G1 的 Release Gate 评审（GO 14/14 + 三方共识 GO + 0 P0/P1/P2）。全部标记"Release阶段不修复，下一版本迭代处理"。

---

## 3. 处置时间线

| 阶段 | TD-V87-001 | TD-V87-002 | TD-V87-003 |
|---|---|---|---|
| Phase01~15 | 引入（编码不一致） | 引入（契约缺失） | — |
| Phase16 | 记录 | 记录 | — |
| Phase17 | rebase 冲突时字节级操作，未修改 | 如实报告不修 | 引入（仿真放大） |
| Phase17 PREP | 交接文档 §3.2 记录 | 交接文档 §3.2 记录 | 交接文档 §3.1 记录 |
| **Phase18** | **本台账登记** | **本台账登记** | **本台账登记 + T1 真实数据替换** |
| V88-RC1 | 文件重编码 | 历史段落修复 | 不再依赖仿真 |

---

## 4. 变更记录

| 版本 | 日期 | 编制人 | 内容 |
|---|---|---|---|
| v1.0 | 2026-10-12 | HERMES Agent (Phase18) | 首次编制，3 项技术债登记 |
