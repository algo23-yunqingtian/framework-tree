# MD5 校验清单

> 任务：`DSHE_V86_ALIAS_ENGINE_PROTOTYPE_AND_CONFLICT_REGRESSION`
> 分支：`feature/v85-chart-template`
> 生成时间：2026-10-01

## 交付物 (5 个)

| # | 文件 | MD5 | 字节 |
|---|---|---|---|
| 1 | `v86_alias_engine_prototype.py` | `E77C8E3692235F1CCE83076920F118C9` | 42,512 |
| 2 | `v86_alias_regression_report.md` | `B3C918070BC306469F63230331689642` | 11,641 |
| 3 | `alias_v86_extended_test_case.json` | `E5147F707FC2C065EFDA9D507123D409` | 20,927 |
| 4 | `alias_task_adapter.py` | `DC88D82E1F6BDF2802EBF4B5091647E3` | 30,024 |
| 5 | `v86_alias_engine_risk_perf_estimate.md` | `2A92953FFF7AEEA45D6EA0B3E8210820` | 12,301 |

## 辅助产出 (2 个, 非交付物)

| 文件 | 说明 |
|---|---|
| `regression_results.json` | 165 条回归原始数据 (自动生成) |
| `test_run_results.json` | 40 条扩展测试运行结果 (自动生成) |

## 校验命令

```powershell
# Windows PowerShell
$dir = "D:\DSH_WORK\framework-tree\analysis\e2e_output\v86\dshe_alias_predev"
Get-ChildItem $dir -File | ForEach-Object {
    $md5 = (Get-FileHash $_.FullName -Algorithm MD5).Hash
    "$md5  $($_.Name)"
} | Out-File "$dir\MD5_CHECKSUM_LIST.txt"
```

```bash
# Linux/macOS
cd /path/to/dshe_alias_predev
md5sum *.py *.md *.json | tee MD5_CHECKSUM_LIST.txt
```

## 冒烟验证

```bash
# 引擎原型冒烟 (17/17 PASS)
python v86_alias_engine_prototype.py --smoke

# 165 条冲突样本回归 (A->R 100%)
python v86_alias_engine_prototype.py --regression

# 扩展测试用例 (37/40 PASS, 3 SKIP)
python v86_alias_engine_prototype.py --run-tests alias_v86_extended_test_case.json

# 任务适配层冒烟 (17/17 PASS)
python alias_task_adapter.py --smoke
```
