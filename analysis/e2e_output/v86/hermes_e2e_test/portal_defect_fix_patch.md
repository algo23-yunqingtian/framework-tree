# SMK-01 / SMK-04 缺陷修复补丁说明

> 工单: `HERMES_V86_PORTAL_DEFECT_FIX_AND_FULL_E2E_INTEGRATION_TEST` · T2.1
> 生成时间: 2026-10-02 10:10
> 修复文件: `analysis/e2e_output/v85/e_api_design/v85_artifact_api.py`
> 基线 commit: `03b3a73`（HERMES 门户集成前置工单）
> 修复后 HEAD: `c7f5a40` → 本工单待提交

---

## 1. SMK-01: repo_root 硬编码 Windows 路径 🔴 阻断 → ✅ 修复

### 1.1 缺陷描述

`v85_artifact_api.py` 的 `ArtifactAPI.__init__` 参数 `repo_root` 默认值硬编码为 `"D:/DSH_WORK/framework-tree"`（Windows 绝对路径）。Linux 部署环境下：

- `ArtifactAPI()` 无参构造 → `self.output_root = Path("D:/DSH_WORK/framework-tree/analysis/e2e_output/v85")` → 不存在 → `RuntimeError: V85 输出根目录不存在`
- `python v85_artifact_api.py --smoke`（无 `--repo-root`）→ 同上崩溃

### 1.2 根因

E 开发环境为 Windows，写死绝对路径；未考虑跨平台部署。

### 1.3 修复方案

新增 `_resolve_default_repo_root()` 函数，三级解析优先级：

```python
def _resolve_default_repo_root() -> str:
    """SMK-01 修复：仓库根解析，消除硬编码路径。"""
    env = os.environ.get("FRAMEWORK_TREE")     # 优先级 1：环境变量
    if env:
        return env
    return str(Path(__file__).resolve().parents[4])  # 优先级 2：相对本文件推导
```

`Path(__file__).resolve().parents[4]` 推导链：

```
parents[0] = e_api_design/
parents[1] = v85/
parents[2] = e2e_output/
parents[3] = analysis/
parents[4] = framework-tree/  ← 仓库根
```

### 1.4 改动清单

| # | 位置 | 改动 |
|---|------|------|
| 1 | 新增 `_resolve_default_repo_root()` | 三级解析：环境变量 → 本文件推导 → 旧硬编码仅做参考常量 `HARDCODED_REPO_ROOT_DEPRECATED` |
| 2 | `ArtifactAPI.__init__` 签名 | `repo_root: str = "D:/DSH_WORK/framework-tree"` → `repo_root: Optional[str] = None` |
| 3 | `__init__` 方法体 | `self.repo_root = Path(repo_root)` → `actual_root = repo_root or _resolve_default_repo_root(); self.repo_root = Path(actual_root)` |
| 4 | CLI `argparse` | `--repo-root` default 从 `"D:/DSH_WORK/framework-tree"` → `None` |
| 5 | CLI `_smoke` 调用 | `return _smoke(args.repo_root)` → `rr = args.repo_root or _resolve_default_repo_root(); return _smoke(rr)` |

### 1.5 修复验证

```
# 无参（原崩溃场景）
$ python3 v85_artifact_api.py --smoke
{
  "smoke": "PASS",
  "repo_root": "/home/ubuntu/framework-tree",
  "artifacts": 31,
  "versions": ["f313570", "v86-dev"],
  "failures": []
}

# 环境变量注入
$ FRAMEWORK_TREE=/home/ubuntu/framework-tree python3 v85_artifact_api.py --smoke
→ 同上 PASS
```

### 1.6 兼容性

- Windows 部署：设置 `FRAMEWORK_TREE=D:/DSH_WORK/framework-tree` 即可（或依赖 `Path(__file__)` 推导，跨平台兼容）
- 显式传参 `--repo-root` 仍有效（向后兼容）
- 旧硬编码常量 `HARDCODED_REPO_ROOT_DEPRECATED` 保留但不再使用，便于代码搜索定位历史

---

## 2. SMK-04: 4 项制品 relpath 过期 ⚠ 警告 → ✅ 修复

### 2.1 缺陷描述

`ARTIFACTS` 白名单表中 4 项制品的 `relpath` 指向 `hermes_portal_gate_final/` 子目录，但实际文件位于其他目录，导致 `exists=False`：

| kind | 原 relpath（过期） | 实际位置 |
|------|-------------------|---------|
| `ambiguous_indicator_list` | `hermes_portal_gate_final/ambiguous_indicator_list.csv` | `alias_lib_full_audit/ambiguous_indicator_list.csv` |
| `template_manifest` | `hermes_portal_gate_final/ths_render_task_manifest.json` | `v85_final_integrate/ths_render_task_manifest.json` |
| `template_task_list` | `hermes_portal_gate_final/ths_render_task_list.json` | `v85_final_integrate/ths_render_task_list.json` |
| `template_task_summary` | `hermes_portal_gate_final/ths_render_task_summary.csv` | `v85_final_integrate/ths_render_task_summary.csv` |

### 2.2 根因

E 编写 ARTIFACTS 表时使用了规划阶段的预期路径，后续 DSHB/HERMES 实际产出时文件落在了不同的子目录。`--smoke` 未校验文件存在性，故未报错。

### 2.3 改动清单

| # | kind | relpath 修改 |
|---|------|-------------|
| 1 | `ambiguous_indicator_list` | `hermes_portal_gate_final/…` → `alias_lib_full_audit/ambiguous_indicator_list.csv` |
| 2 | `template_manifest` | `hermes_portal_gate_final/…` → `v85_final_integrate/ths_render_task_manifest.json` |
| 3 | `template_task_list` | `hermes_portal_gate_final/…` → `v85_final_integrate/ths_render_task_list.json` |
| 4 | `template_task_summary` | `hermes_portal_gate_final/…` → `v85_final_integrate/ths_render_task_summary.csv` |

### 2.4 修复验证

```python
api = ArtifactAPI(token="v85-portal-r-0001")
cat = api.list_artifacts(version="f313570")
missing = [a["kind"] for a in cat["artifacts"] if not a["exists"]]
# 修复前: ["ambiguous_indicator_list", "template_manifest", "template_task_list", "template_task_summary"]
# 修复后: []  ✅ 全部 31 项 exists=True

for kind in ["ambiguous_indicator_list", "template_manifest", "template_task_list", "template_task_summary"]:
    meta = api.get_artifact_meta(kind, version="f313570")
    vf = api.verify_artifact_md5(kind, version="f313570", expected_md5=meta["md5"], verify_file=True)
    assert vf["match"] is True
# 全部 verify_match=True ✅
```

### 2.5 影响范围

- 门户「🔐 快照校验」面板：31/31 全绿（原 27/31）
- 门户「📄 制品目录」Tab：无 ❌ 标记
- 门户「📊 指标大盘」：可正常加载模板清单数据

---

## 3. 联合验证

| 测试 | 修复前 | 修复后 |
|------|--------|--------|
| `--smoke` 无参 | 🔴 RuntimeError | ✅ PASS |
| `--smoke --repo-root /home/...` | ✅ PASS | ✅ PASS |
| 31 项制品存在性 | 27 exists / 4 missing | **31 exists / 0 missing** |
| MD5 实时校验 | 27 match | **31 match** |
| 门户快照面板 | 27/31 绿 + 4 红 | **31/31 全绿** |

---

## 4. 约束合规

- ✅ 修改仅限于 `v85_artifact_api.py`（E 交付的适配层），未修改 V85 任何原始计算结果
- ✅ 未调用 zhiji API
- ✅ 修复是 bug fix（非功能迭代），符合 V85 冻结后「仅允许 bug 修复」规则
- ✅ `ARTIFACTS` 表 relpath 修正属于路径映射修正，不新增/删除制品条目（31 项不变）
