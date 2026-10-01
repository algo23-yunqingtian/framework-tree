# 增强归档打包脚本使用手册

> 脚本: `enhanced_archive_builder.py`
> 工单: `HERMES_V85_PRE_ARCHIVE_PACKAGE_PREP_AND_RELEASE_NOTE`

---

## 1. 功能说明

| 功能 | 说明 |
|------|------|
| 自动复制 | 按目录树复制所有V85产出到归档目录 |
| MD5清单 | 自动生成所有文件的MD5校验清单 |
| Git Tag说明 | 自动生成git tag标记命令说明 |
| 依赖检测 | 检测DSHB sim_sceneA/B等可选文件, 缺失时警告不阻断 |
| 打包报告 | 自动生成打包完整性报告 |

---

## 2. 使用方法

### 2.1 默认运行

```bash
cd /home/ubuntu/framework-tree/analysis/e2e_output/v85/hermes_v85_archive_prep
python3 enhanced_archive_builder.py
```

默认输出到: `/home/ubuntu/framework-tree/v85_final_archive/`

### 2.2 指定基线目录

```bash
python3 enhanced_archive_builder.py --base /home/ubuntu/framework-tree
```

### 2.3 指定输出目录

```bash
python3 enhanced_archive_builder.py --output /path/to/archive
```

### 2.4 完整参数

```bash
python3 enhanced_archive_builder.py \
  --base /home/ubuntu/framework-tree \
  --output /home/ubuntu/backup/v85_archive
```

---

## 3. 输出文件

| 文件 | 说明 |
|------|------|
| MD5_MANIFEST.md | 所有文件MD5校验清单 |
| GIT_TAG_NOTE.md | git tag打标命令说明 |
| ARCHIVE_BUILD_REPORT.md | 打包完整性报告 |
| (子目录) | 按目录树组织的归档文件 |

---

## 4. 目录树

打包脚本按以下目录树复制:

```
v85_final_archive/
├── hermes_v85_final_delivery/      # 最终交付包(9文件)
├── hermes_human_review_tool/       # 人工评审工具(13文件)
├── hermes_portal_gate_final/       # 门户v5+Gate(7文件)
├── hermes_portal_sim_demo/         # 模拟演示(7文件)
├── dshb_full_integrate/            # DSHB全链路整合(5文件)
├── dshb_human_review_prep/         # DSHB人工评审准备(6文件)
├── miss_risk_mining/               # DSHB漏检风险挖掘(6文件)
├── dshb_full_integrate_extra/      # DSHB额外(1文件,可选)
├── dshb_simulation/                # DSHB模拟(2文件,可选)
├── MD5_MANIFEST.md                 # MD5清单
├── GIT_TAG_NOTE.md                 # Tag说明
└── ARCHIVE_BUILD_REPORT.md         # 打包报告
```

---

## 5. 依赖检测

脚本检测以下可选依赖:

| 依赖 | 路径 | 缺失处理 |
|------|------|---------|
| sim_sceneA_result.csv | dshb_simulation/ | ⚠ 警告(自构建替代) |
| sim_sceneB_result.csv | dshb_simulation/ | ⚠ 警告(自构建替代) |
| dshb_final_gate_acceptance.md | dshb_full_integrate_extra/ | ⚠ 警告(Gate v2替代) |

---

## 6. 后续步骤

### 6.1 验证打包

```bash
cd v85_final_archive
cat ARCHIVE_BUILD_REPORT.md  # 查看报告
md5sum -c MD5_MANIFEST.md    # 验证MD5
```

### 6.2 打Git Tag

```bash
cd /home/ubuntu/framework-tree
git tag -a v85-final -m "V85 Final Delivery Package
- 488模板风险管控
- 31条黑名单规则
- 50条风险库v2
- 864条别名库
- 46项Gate检查
- 人工评审工具+Gate预校验
- 3套上线场景(基线/A/B)"
git push origin v85-final
```

### 6.3 压缩归档

```bash
tar -czf v85_final_archive_$(date +%Y%m%d).tar.gz v85_final_archive/
```

### 6.4 异地备份

```bash
mkdir -p /home/ubuntu/backup/v85
cp -r v85_final_archive/ /home/ubuntu/backup/v85/
```

---

## 7. 常见问题

### Q: 脚本报"source directory not found"?

确保在正确路径运行，或指定 `--base /home/ubuntu/framework-tree`。

### Q: 部分文件未复制?

查看 `ARCHIVE_BUILD_REPORT.md` 的"跳过文件"部分，确认源文件是否存在。

### Q: 依赖警告怎么办?

依赖警告不影响打包。DSHB模拟数据未落盘时，使用自构建的场景A/B数据。

### Q: 如何重新打包?

删除 `v85_final_archive/` 目录后重新运行脚本即可。
