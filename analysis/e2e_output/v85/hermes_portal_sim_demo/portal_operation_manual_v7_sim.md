# V85 门户 v7-sim 操作手册（模拟演示版）

> 工单: `HERMES_V85_PORTAL_SIMULATION_DEMO_AND_GATE_DASHBOARD_TUNE`
> 适用门户: `enhanced_review_portal_v6_sim_demo.md`
> v7-sim新增: 场景切换操作说明

---

## 1. 门户入口

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/enhanced_review_portal_v6_sim_demo.md
```

---

## 2. 场景切换操作（v7-sim新增）

### 2.1 进入场景切换控件

打开门户 §0，点击场景切换控件：

```
[ 基线(当前) ]  [ 场景A: 最小放行 ]  [ 场景B: 完整处置 ]
```

### 2.2 切换到场景A

1. 点击「场景A: 最小放行」
2. 门户自动加载场景A模拟数据
3. Gate大盘刷新为: H1✅ H2❌ H3❌ H4❌ H5✅
4. 剩余阻塞: 7条独立阻塞
5. 结论: ⚠ 可临时豁免H2/H3/H4上线

### 2.3 切换到场景B

1. 点击「场景B: 完整处置」
2. 门户自动加载场景B模拟数据
3. Gate大盘刷新为: H1✅ H2✅ H3✅ H4✅ H5✅
4. 剩余阻塞: 1条可豁免
5. 结论: ✅ 允许合并+上线

### 2.4 回切基线

点击「基线(当前)」恢复真实状态。

---

## 3. Gate看板交互（调优新增）

### 3.1 下钻操作

点击Gate阻塞项（如H1 ❌ BLOCKED）：
1. 展开剩余阻塞条目计数
2. 显示阻塞原因悬浮提示
3. 显示预估工时
4. 显示可豁免标记
5. 提供跳转人工评审工作台链接

### 3.2 悬浮提示示例

| Gate | 悬浮提示 |
|------|---------|
| H1 | "864条高置信候选待回写, 预估1天" |
| H2 | "4条漏拦截需优先: RISK-002/010/011/013" |
| H3 | "依赖H1+H4解除, 预估D+4" |
| H4 | "总工时5-7天, 建议优先级: A→B→C" |

### 3.3 可豁免标记

| 标记 | 含义 |
|------|------|
| ⚠ 可豁免 | 临时放行可上线 |
| ❌ 不可豁免 | 硬阻塞, 必须解除 |

---

## 4. 演示数据包操作

### 4.1 查看演示数据包

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/demo_data_package.md
```

### 4.2 加载场景A数据

```bash
python3 gate_pre_check.py --scene A
```

### 4.3 加载场景B数据

```bash
python3 gate_pre_check.py --scene B
```

---

## 5. Gate场景报告操作

### 5.1 查看场景A报告

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/gate_sceneA_report.md
```

### 5.2 查看场景B报告

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/gate_sceneB_report.md
```

### 5.3 查看场景对比

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/gate_scenario_compare.md
```

---

## 6. 验收演示脚本操作

### 6.1 查看演示脚本

```bash
cat analysis/e2e_output/v85/hermes_portal_sim_demo/v85_accept_demo_script.md
```

### 6.2 按脚本执行演示

1. 按脚本步骤逐一操作
2. 话术按脚本念读
3. 切换场景按脚本指示
4. 展示Gate变化按脚本标注
