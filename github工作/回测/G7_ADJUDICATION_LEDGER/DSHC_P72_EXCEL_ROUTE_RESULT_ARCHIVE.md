# DSHC-P72 今日 Excel 拉数结果归档

**归档时间**: 2026-10-16 23:50 GMT+8  
**工单**: DSHC-P72  
**状态**: `EXCEL_ROUTE_PERMITTED_NO_NEW_SUCCESSFUL_SAMPLE`  
**Gate**: `CLOSED/HOLD`  
**Release Permit**: `NOT_ISSUED`  
**Wind API Calls**: `0`

---

## 1. 结论

DSHA 今日以 Excel + 万得插件路线为主路径执行最小验证。当前台账证据显示：

- Excel / WDF 插件路线未成功完成 WSD/WSS 小样拉取；
- 已记录阻塞为 COM / 插件加载 / 管理员前置条件问题；
- 今日未新增成功归档的小样因子数据；
- 未触发批量分片回测；
- 未触发全量回测；
- 未切换 WindPy 原生通道；
- 未修改任何凭证。

---

## 2. 观察依据

| 依据 | 结果 |
|---|---|
| `data-harbor/dsha_p49_prep/P49_backtest_audit/excel_wind_test_report.md` | WSD/WSS 公式 BLOCKED；Excel add-in registered but not loaded |
| `data-harbor/dsha_p49_prep/P49_backtest_audit/wind_fix_log.md` | WDF COM 未注册 / Wind add-in 未加载；InitWAPI.exe 需要管理员 |
| `G7_ADJUDICATION_LEDGER/DSHD_P67_WIND_TEST_AUDIT_NOTES.md` | 记录 COM 未注册、插件无法加载、需要管理员 |
| `G7_ADJUDICATION_LEDGER/DSHD_P67_MONITOR_LOG.jsonl` | 持续审计；不写入明文凭据 |

---

## 3. 今日处置

- 已下发现场执行许可：`G7_ADJUDICATION_LEDGER/DSHC_P72_EXCEL_ROUTE_PERMIT.md`
- 已保存明天人工操作提示：`TO_HUMAN_RUN_ME/DSHC_P72_INITWAPI_ADMIN_RUN_PROMPT.md`
- 已更新缺陷台账：`G7_ADJUDICATION_LEDGER/DSHD_DEFECT_OBSERVATION_REGISTRY.md`
- 已刷新校验：`G7_ADJUDICATION_LEDGER/SHA256_CHECKSUMS.txt`

---

## 4. 明日前置条件

明天人工管理员需先运行：

```text
D:\bin\InitWAPI.exe
```

要求：

- 右键；
- 以管理员身份运行；
- UAC 点「是」；
- 完成后回复：`已执行管理员InitWAPI，请执行连通测试`

完成后才能评估 WindPy 原生通道切换；在此之前，批量回测仍保持 CLOSED。
