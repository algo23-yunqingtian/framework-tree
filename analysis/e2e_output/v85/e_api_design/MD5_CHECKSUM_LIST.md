# E 任务交付物 MD5 清单

> 任务：`E_V85_READONLY_API_AND_V86_BACKEND_DESIGN`
> 分支：`feature/v85-chart-template`
> 基线：HERMES `a2815c4` / DSHB `6771406` / DSHE `f313570`
> 目录：`analysis/e2e_output/v85/e_api_design/`
> 约束：`NO_ZHIJI_API_CALL=TRUE` / `READ_ONLY=TRUE` / `NO_MODIFY_SOURCE=TRUE` / `NO_GT_MODIFICATION=TRUE`
> 生成时间：2026-10-01

## 1. 五份指定交付物

| # | 文件 | 字节 | MD5 |
|---|---|---|---|
| 1 | `api_spec_v85_readonly.md` | 14,888 | `78466F531F8CEDF2C0CFD4B3F1E3EBE4` |
| 2 | `v85_artifact_api.py` | 45,493 | `2CA6020D3BDB2E6A9BA7A1F44F96B8C3` |
| 3 | `v86_backend_schema_design.md` | 19,119 | `F30ACFF6607ACA611899CB3F52013683` |
| 4 | `v86_task_api_design.md` | 15,814 | `7E23F29F92FE612AD3401D90BEAA2A75` |
| 5 | `v85_to_v86_migration_verify_plan.md` | 22,420 | `4BE6A78B898485A08ACDE951F555EDD2` |

**合计**：5 文件 / 117,734 字节

## 2. 验证命令

```bash
cd analysis/e2e_output/v85/e_api_design/
md5sum api_spec_v85_readonly.md v85_artifact_api.py v86_backend_schema_design.md \
       v86_task_api_design.md v85_to_v86_migration_verify_plan.md
# 期望输出（顺序对齐上表）：
#   78466f531f8cedf2c0cfd4b3f1e3ebe4  api_spec_v85_readonly.md
#   2ca6020d3bdb2e6a9ba7a1f44f96b8c3  v85_artifact_api.py
#   f30acff6607aca611899cb3f52013683  v86_backend_schema_design.md
#   7e23f29f92fe612ad3401d90beaa2a75  v86_task_api_design.md
#   4be6a78b898485a08acde951f555edd2  v85_to_v86_migration_verify_plan.md
```

## 3. 冒烟自检

```bash
python v85_artifact_api.py --smoke
# 期望输出：
# {
#   "smoke": "PASS",
#   "artifacts": 31,
#   "versions": ["f313570", "v86-dev"],
#   "failures": []
# }
```

冒烟测试覆盖：健康检查 / 版本列表 / 元数据 / MD5 校验 / 查询 / 写保护 / 权限 / 路由分发。
