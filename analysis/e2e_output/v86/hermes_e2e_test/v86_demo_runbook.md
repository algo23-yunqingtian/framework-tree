# V86 原型验收演示脚本（Runbook）

> 工单: `HERMES_V86_PORTAL_DEFECT_FIX_AND_FULL_E2E_INTEGRATION_TEST` · T2.5
> 生成时间: 2026-10-02 10:35
> 分支: `feature/v85-chart-template`
> 适用: V86 原型评审演示，可直接执行

---

## 演示环境准备

### 0.1 环境要求

| 项 | 要求 |
|---|---|
| OS | Linux (Ubuntu 22.04+) |
| Python | 3.10+ |
| 仓库 | `framework-tree` @ `feature/v85-chart-template` |
| 环境变量 | `FRAMEWORK_TREE=/home/ubuntu/framework-tree`（可选，不设则自动推导） |
| 网络 | 无需外网（零 zhiji 调用） |

### 0.2 启动步骤

```bash
# 1. 同步基线
cd /home/ubuntu/framework-tree
git fetch origin
git checkout feature/v85-chart-template
git pull --rebase origin feature/v85-chart-template

# 2. 验证 SMK-01 修复（无参冒烟）
cd analysis/e2e_output/v85/e_api_design
python3 v85_artifact_api.py --smoke
# 期望输出: {"smoke": "PASS", "repo_root": "/home/ubuntu/framework-tree", "artifacts": 31, ...}

# 3. 验证 SMK-04 修复（31 项全存在）
python3 -c "
from v85_artifact_api import ArtifactAPI
api = ArtifactAPI(token='v85-portal-r-0001')
cat = api.list_artifacts(version='f313570')
missing = [a['kind'] for a in cat['artifacts'] if not a['exists']]
print(f'制品: {cat[\"count\"]} / 缺失: {len(missing)}')
assert len(missing) == 0, f'仍有缺失: {missing}'
print('✅ SMK-04 修复验证通过')
"
# 期望输出: 制品: 31 / 缺失: 0  ✅ SMK-04 修复验证通过

# 4. 启动本地预览
cd /home/ubuntu/framework-tree
python3 -m http.server 8766
# 访问 http://124.221.113.37:8766/nickel-gh/
```

---

## 演示流程（5 个场景，约 15 分钟）

### 场景 1: V85 冻结门户 🔒（3 分钟）

**目标**: 展示 V85 冻结门户的数据完整性与只读保护

#### 步骤 1.1: 版本横幅

打开 `http://124.221.113.37:8766/nickel-gh/`，观察顶部红色横幅：

```
🔒 V85.0 FROZEN
version_tag: v85.0   commit: f313570   tag: v85-final-persist @ da2a440
31 规则 / 864 别名 / 50 风险 / 488 模板 / 31 制品已登记
⚠️ 本环境为只读演示环境，所有编辑功能已禁用，数据由冻结快照提供
```

**讲解**: V85 已冻结，所有数据通过只读 API 提供，门户不持有本地副本。

#### 步骤 1.2: 快照 MD5 校验

点击「🔐 快照校验」→ 「全量校验」：

```
| 制品 kind          | 快照 MD5     | API 实时 MD5  | 校验 |
| risk_db            | 2c85f402…    | 2c85f402…     | ✅   |
| ...（31 项）       |              |               |      |
汇总: 通过 31/31 ✅
```

**讲解**: 31 项制品 MD5 全部 match，证明 V85 冻结数据未被篡改。

#### 步骤 1.3: 只读保护验证

尝试调用写方法（终端演示）：

```bash
python3 -c "
from v85_artifact_api import ArtifactAPI
api = ArtifactAPI(token='v85-portal-r-0001')
try:
    api.list_artifacts(version='v86-dev')
except Exception as e:
    print(f'✅ 版本隔离: {e.code if hasattr(e,\"code\") else type(e).__name__}')
"
```

**期望**: `✅ 版本隔离: VERSION_READ_FORBIDDEN`

---

### 场景 2: V85/V86 对比面板 📈（3 分钟）

**目标**: 展示双版本指标对比 + 口径切换消除歧义

#### 步骤 2.1: 原型口径对比

点击「📈 V85/V86 对比」Tab，默认展示「原型对比」口径：

```
⚠️ 口径提示: 当前对比为「V86 P0 原型(4规则) vs V85 完整黑名单(31规则)」
4 条回归源于规则集差异，非能力退化。

P0 拦截率: V85 87.5% → V86 75.0%  Δ −12.5pt
TP: 44 → 40  FP: 0 → 0  回归: 4
```

**讲解**: 75% < 87.5% 不是退化，是原型只有 4 条规则 vs 基线 31 条。4 条回归中 3 条是上游数据缺失（DATA_MISSING），1 条是原型无对应规则。

#### 步骤 2.2: 切换完整口径

切换到「完整对比」口径：

```
✅ 完整对比结果:
P0 拦截率: V85 88.2% → V86 100%  Δ +11.8pt
TP: +7  FP: 0  回归: 0
✅ 上线准入达标
```

**讲解**: V86 完整黑名单（35 规则）在 V85 基础上新增 BL-009a + BL-026，拦截率提升到 100%，0 回归 0 误拦。

#### 步骤 2.3: 回归明细表

展示 4 条回归的口径说明列：

```
| RISK-022 | BL-019 → PASSED    | 🔴 原型无 BL-019（完整版有） |
| RISK-001 | BL-005 → DATA_MISSING | 🟡 上游 matched_name 缺失 |
| RISK-003 | BL-003 → DATA_MISSING | 🟡 上游 matched_name 缺失 |
| RISK-006 | BL-002 → DATA_MISSING | 🟡 上游 matched_name 缺失 |
```

---

### 场景 3: V86 测试样本面板 🧪（3 分钟）

**目标**: 展示 48 用例测试套件的可视化

#### 步骤 3.1: 用例浏览

点击「🧪 测试样本」Tab：

```
过滤: [规则 ▾ BL-009a]  [类型 ▾ 全部]  [风险 ▾ P0]

BL-009a 正向触发用例 (4 条)
  ☑ TC-BL009A-001  正向 P0  碳酸锂 三元523需求 → SMM:碳酸锂现金生产利润  expected: BLOCKED
  ☑ TC-BL009A-002  正向 P0  碳酸锂需求总量 → 碳酸锂冶炼利润  expected: BLOCKED
  ⚠ TC-BL009A-NEG-001 负向 安全  同口径匹配  expected: PASSED
  ▸ TC-BL009A-BND-001 边界  压力测试  expected: 视case
```

#### 步骤 3.2: 单条 case 预览

点击 `TC-BL009A-001`，右侧预览：

```
case_id: TC-BL009A-001
类型: positive_trigger (正向危险样例)
indicator_name: 碳酸锂 三元523需求
matched_name: SMM: 碳酸锂现金生产利润: 外购三元极片黑粉
expected_result: BLOCKED
expected_rule: BL-009a
risk_level: P0
source_risk: RISK-002
description: 原始RISK-002案例：需求→利润反向，BL-009a应拦截

[▶ 单条执行] [批量执行]
```

#### 步骤 3.3: 期望分布

展示 48 用例的期望分布饼图：

```
BLOCKED:      24 (50.0%) 🔴
PASSED:       17 (35.4%) 🟢
DATA_MISSING:  7 (14.6%) 🟡
```

---

### 场景 4: V86 双任务面板 🚀（3 分钟）

**目标**: 展示规则 + 别名双任务提交

#### 步骤 4.1: DSHB 规则任务

点击「🚀 异步任务」→ 选择「🧪 DSHB 规则任务」：

```
规则集: [v86-p0-prototype (4规则) ▾]
场景: [A ▾]    用例集: [v86-rule-test-suite-v1 (48用例) ▾]
[▶ 提交规则任务]
```

**讲解**: 提交后任务进入 queued → running（进度环）→ succeeded → 结果注入对比面板。

#### 步骤 4.2: DSHE 别名任务

切换到「🔤 DSHE 别名任务」：

```
引擎变体: [F3+F4 ▾]
别名列表:
  COMEX:铜:主力合约:收盘价(日
  沪铜主力收盘价
  碳酸锂 三元523需求
[▶ 提交别名任务]
```

**讲解**: 解析结果以 canonical_key + confidence 展示。

#### 步骤 4.3: 联合结果

展示别名 → 规则的联合三联表：

```
| alias                | canonical_key      | 规则状态 | 命中规则 |
| COMEX:铜:主力合约…  | cu_23_comex_close  | PASSED  | —       |
| 碳酸锂 三元523需求  | li_523_demand      | BLOCKED | BL-009a |
| 沪铜主力收盘价       | cu_23_comex_close  | PASSED  | —       |
汇总: 解析 3/3 (100%) | 拦截 1/3 (33.3%) | TP 1 | FP 0
```

---

### 场景 5: E2E 冒烟总结 📋（3 分钟）

**目标**: 展示 18 项冒烟 + 4 大 E2E 场景汇总

#### 步骤 5.1: 冒烟结果

```
冒烟 18 项: 13 PASS / 1 FAIL(已修复) / 4 WARN
- SMK-01 repo_root 硬编码: ✅ 已修复（无参 PASS）
- SMK-04 4项制品relpath过期: ✅ 已修复（31/31 exists）
- V85 API 10项实测: health/versions/31制品/query50+2721行/MD5 match/隔离403/写拒绝
```

#### 步骤 5.2: E2E 4 大场景

```
场景1 V85基线查询: ✅ PASS (7/7)
场景2 V86规则引擎: ✅ PASS (48用例/13组/V86RuleEngine加载)
场景3 V86别名引擎: ⚠ PARTIAL (audit_kit依赖缺失，DSHE自测17/17 PASS)
场景4 联合场景:    ⚠ PARTIAL (别名引擎环境依赖)
```

#### 步骤 5.3: 缺陷汇总

```
| SMK-01 | repo_root 硬编码 | 🔴→✅ 已修复 |
| SMK-04 | 4项relpath过期  | 🟡→✅ 已修复 |
| SMK-09 | 写方法TypeError  | 🟡 待修复   |
| E2E-D01| audit_kit缺失   | 🟡 待DSHE提供 |
| E2E-D02| V86任务API无实现 | 🔴 外部依赖  |
```

---

## 演示备注

### A. 降级说明

| 功能 | 当前状态 | 演示方式 |
|------|---------|---------|
| V85 冻结门户 | ✅ 完全可用 | 实时演示 |
| V85/V86 对比面板 | ✅ 离线样本可用 | 实时演示（`comparison_report.json`） |
| V86 测试样本面板 | ✅ 可用 | 实时演示（`v86_rule_test_suite.json`） |
| V86 双任务面板 | ⚠ 任务 API 未实现 | 表单展示 + 离线结果回显 |
| V86 别名引擎进程内调用 | ⚠ `audit_kit` 缺失 | 展示 DSHE 自测 17/17 PASS 记录 |

### B. 约束合规

- ✅ 零 zhiji API 调用
- ✅ V85 基线只读，未修改任何计算结果
- ✅ 仅新增文档 + bug 修复
- ✅ 分支锁定 `feature/v85-chart-template`

### C. 预期问答

| 问题 | 回答 |
|------|------|
| V86 P0 拦截率 75% 比 V85 低？ | 口径不同：4 规则 vs 31 规则。完整 35 规则时 100%。 |
| 为什么别名引擎不能直接跑？ | `audit_kit` 模块是 DSHE 开发环境依赖，需 DSHE 提供。 |
| V86 任务 API 什么时候上线？ | E 负责实现，门户已定义降级路径。 |
| V85 什么时候合并 main？ | 人工评审解除 H1/H2/H3/H4 后合并（预估 5-7 天）。 |
