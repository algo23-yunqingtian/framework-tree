# DSHC-P72 Excel 路线执行许可 / Excel Route Execution Permit

**签发时间**: 2026-10-16 23:50 GMT+8  
**签发 Agent**: DSHC-P72  
**执行接收方**: DSHA  
**当前分支**: `feature/v88-g1`  
**工单**: DSHC-P72 执行工单｜Excel路线调度 + 台账同步 + 待明天人工激活

---

## 1. 硬性约束

| 项目 | 状态 |
|---|---|
| Global Gate | **CLOSED/HOLD** |
| Release Permit | **NOT_ISSUED** |
| Wind API Calls | **0** |
| 全量回测 / 批量分片回测 | **CLOSED / 禁止** |
| WindPy 原生通道 | **HOLD / 等待明天人工管理员 InitWAPI** |
| Excel + 万得插件路线 | **今日主路径 / 允许执行最小样本报送** |
| 凭证轮换 | **DEFERRED_TO_LAUNCH / 不修改密码** |
| 现有账号 | **测试沿用，不触发密码修改** |
| 自动提权 / 绕过 UAC | **禁止** |
| 审计记录 | 所有操作写入 `G7_ADJUDICATION_LEDGER/dshd_p67_monitor_log.jsonl` |

---

## 2. 给 DSHA 的执行许可

DSHA 可以今天优先走 **Excel + 万得插件路线**，但仅限：

1. 插件可用性检查；
2. Excel 基础公式可用性检查；
3. 单点 / 小样 WSD 或 WSS 查询验证；
4. 失败阻塞记录；
5. 小样结果归档；
6. 台账与监控日志记录。

DSHA **不得**执行：

1. 批量分片拉数；
2. 7 表 / 108 calls 级 Wind 查询；
3. 全量回测；
4. HOLD 因子计算；
5. 任何自动提权、管理员提权、绕过 UAC 或绕过 Wind 初始化的尝试；
6. 任何密码修改 / 凭证轮换动作。

---

## 3. 今日观察结论

当前已有 DSHA 回报显示：

- WindPy 原生路径仍受阻塞；
- Excel WDF / 万得插件路径不可用或无法完成 WSD/WSS 查询；
- 阻塞特征符合 `COM 未注册 / 插件无法加载 / 需要管理员` 之一；
- 今日未形成新的 Excel 小样因子成功归档；
- `wind_api_calls` 保持 **0**；
- 全量回测未启动；
- `release_permit` 保持 **NOT_ISSUED**。

因此，今日交付口径为：

> Excel 路线许可已下发；批量闸门保持 CLOSED；因插件/COM/管理员前置条件未满足，今日未归档新的成功小样因子；全部等待明天人工执行 `D:\bin\InitWAPI.exe`。

---

## 4. DSHC 处置

- DEFECT-004 更新为 `BLOCKED_WAIT_HUMAN_ACTION`；
- DEFECT-005 保持 `OPEN / DEFERRED_TO_LAUNCH`；
- DEFECT-003 确认 `RESOLVED`；
- 明天提示已保存到 `TO_HUMAN_RUN_ME/DSHC_P72_INITWAPI_ADMIN_RUN_PROMPT.md`；
- 禁止今天执行提权或自动初始化。
