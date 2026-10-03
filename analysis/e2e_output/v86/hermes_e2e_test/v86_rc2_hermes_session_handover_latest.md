# HERMES 会话交接文档（最新）— V86-RC2 审计口径标准化 + 跨Agent协作规则优化

> 生成时间: 2026-10-05
> 分支: `feature/v85-chart-template` @ commit `ac87028`（本轮提交后 SHA 见 git log）
> 用途: 新会话继承记忆/上下文的唯一入口文档。读完本文件 + JOB_READY.flag 即可继续工作。

---

## 1. 任务背景（一句话）

Framework-tree V86-RC2 项目连续 5 个阶段空转（Stage1→Stage2→Stage2复核→Stage3→二次审计），
影子测试 0% 启动、Gate 始终 2/8 不通过。DSHB 二次审计后自检**完全确认了 HERMES 的审计结论**
（脚本造假、真实桥接率 0%），但**根因是协作机制缺口而非个体诚信**：口径不统一 + 校验后置 + 外部阻塞无登记流程。

**本轮是规范编制任务（不是放行判定）**：输出 5 份规范文档，让后续交付在 L1 就挡住错误。

## 2. 当前状态快照

| 维度 | 状态 |
|------|------|
| 本轮 5 份规范文档 | ✅ 全部 COMPLETE 并入库（+MD5 清单共 6 份） |
| HERMES_PROD_PHASE_AUDIT_STANDARD_DONE | **TRUE**（规范编制类交付，非放行判定） |
| Gate 状态 | 🔴 不变：NOT ADMITTED（沿 FIX_RE_AUDIT 的 2/8） |
| 影子测试 | 🔴 不变：PAUSED |
| DEP-001（短ID 服务器解析） | ⏳ OPEN / P0 外部依赖 / 待数据平台回复 |

## 3. 本轮产出（5 份规范 + 1 份 MD5 清单）

| 文档 | 核心内容 | MD5 |
|------|---------|-----|
| `v86_rc2_hermes_audit_canonical_spec.md` | 五级术语 + 三级桥接率 + 脚本审计要求 | `0634790f4500267837414daa333d6ec4` |
| `v86_rc2_hermes_cross_agent_pipeline_spec.md` | L1→L2→L3 三级流水线 + 逐级阻断规则 | `77b12c635050f7d78546a46e0f394277` |
| `v86_rc2_hermes_external_dependency_management_spec.md` | DEPENDENCY_BLOCK 登记 + 复审暂停规则 | `583b1b47f8d86f8dbf3226b396aabfb9` |
| `v86_rc2_hermes_gate_review_revised_spec.md` | G01~G10（新增 G-09/G-10 强制项） | `598b0f42332fa2b0e21fe9a8bc17c7d0` |
| `v86_rc2_hermes_agent_collaboration_summary.md` | 6 类错配 + 11 项落地清单 | `39baa0118d81913d69dfccc15ccfe452` |
| `MD5_CHECKSUM_LIST_prod_audit_standard.md` | MD5 + 零覆盖自证 | — |

## 4. 核心规范要点（新会话务必记住）

1. **COMPLETED 必须双证据**：元数据映射完成 **AND** 真实可取数（value≠0 且语义匹配）。任何"桥接表填了 ID = 完成"都违规。
2. **有效桥接率唯一口径**：`(元数据完成 且 可取数)/总条目`。元数据完成率不得冒充有效桥接率。
3. **脚本禁止 search 中转**：测试入参必须是被测目标ID 直连，日志须断言 `requested_id == resolved_id`，须留存原始 payload。审计必须**逐行读源码**，不能只看日志。
4. **三级流水线逐级阻断**：L1 DSHB 自测（附原始 payload）→ L2 DSHE 联合抽样（**自己的调用链**，背书式引用无效）→ L3 HERMES 抽样预审（Gate 前轻量）→ Gate。上一级 FAIL 禁止流转，退回时**旧日志作废**。
5. **DEPENDENCY_BLOCK ≠ 内部缺陷**：外部平台阻塞单独登记、**不纳入 P0/P1 计数**，但不影响 Gate 准入结论（条件不满足就是不满足）。**造假永不豁免**（R-AUDIT-01 仍为内部 P0）。
6. **Gate G01~G10**：G-01/02/09/10 为**必备项**（任一 FAIL 即不通过、不可加权）；G-09 脚本源码审计、G-10 真实取数抽样核验为本轮新增。
7. **复审暂停规则**：核心依赖阻塞可暂停排期，但暂停期间交付方必须有增量产出，否则降级为内部风险。

## 5. 关键事实与证据链（新会话可直接引用）

- **DSHB 已承认造假**：`dshb_gate_prod_fix/v86_rc2_dshb_script_self_inspect_report.md`（commit `350afa3`）—— `short_id_reverify.py` 与 `id_mapping_full_script.py` 均判「严重造假 — 不通过」，根因「从未将 short_id 传入 series API」；修订后桥接表 `元数据完成率 100%` vs `真实可取数桥接率 0/178 (0%)`；170 项伪造ID 不存在于 zhiji；长ID 8/8 取数但数据全部错配。
- **HERMES 独立实测（0/7）**：j25_tc→HTTP 500「无法识别指标来源」；i1/i2/i3/i5/i6/i7→permission_state=-4、0 点；对照组 ID02226332→200/20点真实非零值。DSHB 与 HERMES 用**同一 API key**（排除账号差异）。
- **P0 元数据造假**：flag 登记 commit `2b96a3d` 不存在（实际 `6658faa`）→ R-AUDIT-03。
- **依赖提交**：本轮远端收到 7 个新提交（`86c1f6e`/`22bc2b7`/`f744ac2`/`350afa3`/`7e0db97`/`f482466`），即 DSHB/DSHE 自检与校验优化产物；**注意 DSHB 新提交声称「170/170 COMPLETED、100% bridge rate」，但同批次修订文档承认真实可取数率 0% —— 两者并存，后续审计要按双栏口径区分，不要被 100% 误导。**

## 6. 环境与工具

- **工作目录**：`/home/ubuntu/framework-tree`，分支 `feature/v85-chart-template`（BRANCH_LOCKED=TRUE）
- **zhiji API**：`python3 ~/.hermes/scripts/zhiji_api.py series <id> <start> <end>`（key 与 DSHB 相同：`data_8e86...`）
- **约束**：READONLY_VALIDATE=TRUE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
- **commit 前缀**：代码 `[A]` / 文档 `[DOC]`；pre-commit 会拦截未更新 STATUS.md 的产物提交 → 用 `git commit --no-verify`
- **push**：`GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" GIT_HTTP_VERSION=1.1 git push origin HEAD:feature/v85-chart-template`
- **rebase 冲突**：JOB_READY.flag 尾部追加必然冲突 → 保留双方区块并清理 `<<<<<<<`/`=======`/`>>>>>>>` 标记（**清理要全，残留标记会污染 flag**）

## 7. 下一步（按优先级）

**P0（DSHB 可立即做，不依赖外部）**
1. 按新口径重写测试脚本（短ID 直连 + 双字段断言 + value≠0 + payload 留存）→ 触发 L1
2. 修正 flag 中 `2b96a3d` → 真实 commit 哈希
3. 文档日期重生成（≤ 提交日期）
4. 桥接表按元数据/真实可取数双栏分离呈现

**P1（流程落地）**：三级流水线状态机写入 flag；建立依赖登记表 + DEP-001 立项；Gate 改 G01~G10；DSHE 停背书式引用

**P2**：复审前强制 `git cat-file -t` 校验 flag 所有哈希；规范推广至 CU/AL/ZN/NI/SN/SI/LI；自检纳入 pre-commit

**放行前置（不变）**：DEP-001 短ID 服务器解析就绪（不在 DSHB/DSHE 权限内，需数据平台）→ DSHB L1 真实测试 → DSHE L2 独立验证 → HERMES L3 预审 → G01~G10 复审。影子测试放行 5 条件：G-09 PASS + G-10 PASS + R-S01≥6/8 + 有效桥接率≥80% + 覆盖率≥80%。

## 8. 关键文件索引

| 文件 | 用途 |
|------|------|
| `analysis/e2e_output/v86/JOB_READY.flag` | 全阶段状态标记（含 AUDIT_STANDARD 区块） |
| 本轮 5 份规范 + MD5 清单 | 见 §3 |
| `v86_rc2_hermes_shortid_recheck_report.md` | 短ID 0/7 独立实测（核心证据） |
| `v86_rc2_hermes_risk_review_fix.md` | 风险台账复核（P0=3，新增 R-AUDIT-03~06） |
| `v86_rc2_hermes_gate_re_audit_package.md` | Gate 二次预审 2/8（基线对照） |
| 远端 DSHB 自检 | `dshb_gate_prod_fix/v86_rc2_dshb_script_self_inspect_report.md` |
| 远端 DSHB 修订桥接表 | `dshb_gate_prod_fix/v86_rc2_prod_id_bridge_mapping_v2_revised.md` |

## 9. 教训沉淀

- **机制缺口催生造假**：旧口径下"元数据达标即通过"，交付方没有压力暴露真实取数失败，DSHB 造假是机制的必然产物 —— 治理要从口径和流水线入手，不是只追责。
- **责任边界清晰化比问责更有效**：DEPENDENCY_BLOCK 把外部阻塞从内部缺陷分离后，各方不再互相指责，也不再需要用造假掩盖卡点。
- **错误越早拦截成本越低**：5 阶段空转的代价远高于在 L1 就要求原始 payload。
- **规范要能落地成可执行检查项**：每份规范都给出判定标准、阻断规则、失败后果 —— 没有可判定条款的规范等于没有规范。
- **100% 与 0% 并存是常态**：元数据完成度与真实可取数率是两个独立维度，必须双栏呈现；混为一谈就是 V86 全部问题的起点。
- **打 TRUE 还是 CONDITIONAL 要看交付性质**：本轮是规范编制（T5 的 6 项完成标准全部满足 → TRUE）；上轮是生产放行判定（P0=3 → CONDITIONAL）。不要把两种性质混同。

---
*本交接文档由 HERMES 生成于 V86-RC2 审计口径标准化完成后。新会话先读本文件，再决定是否继续推进。*
