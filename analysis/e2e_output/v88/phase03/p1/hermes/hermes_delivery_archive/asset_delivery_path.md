# 资产交付路径清单 (asset_delivery_path.md)

> **TASK_ID**: V88_PHASE03_P14_HERMESHF_P13_VISUAL_ASSET_DELIVERY_CLOSE
> **AGENT**: HERMEShf
> **生成**: 2026-10-17T21:21 +0800
> **交付对象**: DSHE (自动化 QC)
> **状态**: DELIVERED (待 DSHE 拉取)

---

## 一、交付资产包总览

| 包名 | 大小 | MD5 | 用途 |
|------|----:|-----|------|
| `visual_asset_shturl.cc.zip` | 11539B | `8e12412c4971068c37670ca741991b76` | 封签 6 项交付物（P13 工单资产） |
| `visual_asset_shturl.H.zip` | 956458B | `0106b66baab452349442df3b747f504e` | 完整可视化资产包（图表+部署+脚本+报告，供 QC 全量校验） |

**SHA256 完整哈希**:
```
visual_asset_shturl.cc.zip: 0b17585300f9aa903ed06d9a80c6651e7885d1790f097bae5909fd4eb683fc0a
visual_asset_shturl.H.zip:  a2dbcb341ad291ae915e949d5a4e603393476375e1c0c810e6f9172a64bc280e
```

## 二、文件绝对路径（DSHE 拉取入口）

### 2.1 交付归档目录
```
/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_delivery_archive/
```

### 2.2 两个资产包

| 包 | 绝对路径 |
|----|---------|
| 封签 6 项 | `/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_delivery_archive/visual_asset_shturl.cc.zip` |
| 完整资产包 | `/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_delivery_archive/visual_asset_shturl.H.zip` |

### 2.3 原始交付物（未打包，可直接访问）

**P13 封签归档 (hermes_final_seal_archive/)**
```
/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_final_seal_archive/
├── chart_asset_recheck_report.md    # 22/22 复核项 PASS
├── cleanup_shturl                    # 临时缓存清理记录
├── hermes_asset_index.md             # 可视化模块资产索引
├── MD5_MANIFEST.md                   # 本地哈希清单 (34 文件)
├── STATUS.md                         # P13 状态
└── JOB_READY.flag                    # 就绪标记
```

**P12 可视化资产 (hermes_web_dashboard_archive/)**
```
/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_web_dashboard_archive/
├── web_asset/                          # 10 文件 (5 PNG + 5 HTML)
├── github_pages/                       # GitHub Pages 部署结构
├── github_pages_deploy.zip             # 一键部署包 (314KB)
├── phase03_weekly_report.md            # 周报副本
├── global_gate_dashboard_v9.md         # 看板 v9
└── final_verification_report.md        # P12 验证报告
```

**顶层脚本与周报**
```
//
├── chart_lib.py
├── build_charts.py
├── build_html_charts.py
├── phase03_weekly_report.md
└── web_asset/                          # 顶层源 (周报引用)
```

## 三、DSHE QC 拉取步骤

```bash
# 1. 拉取封签包
cd /home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_delivery_archive
md5sum visual_asset_shturl.cc.zip
# 期望: 8e12412c4971068c37670ca741991b76

unzip -l visual_asset_shturl.cc.zip
# 期望: 6 文件 (MD5_MANIFEST.md / STATUS.md / JOB_READY.flag / chart_asset_recheck_report.md / cleanup_shturl / hermes_asset_index.md)

# 2. 拉取完整资产包
md5sum visual_asset_shturl.H.zip
# 期望: 0106b66baab452349442df3b747f504e

unzip -l visual_asset_shturl.H.zip
# 期望: 29 文件 (web_asset/ + github_pages/ + 脚本 + 周报)

# 3. 校验 5 PNG 主色 #6B4C9A SOLID
# 校验 5 HTML 无渐变/无圆角/无阴影
# 校验 34 文件哈希与 MD5_MANIFEST.md 一致
```

## 四、MD5_MANIFEST.md 追加确认

全局 MD5_MANIFEST.md (`/home/ubuntu/framework-tree/MD5_MANIFEST.md`) 已追加 P13 段（34 文件 MD5+SHA256）。

**追加验证**:
- 新增行数: 41 行（表头 + 34 文件 + 尾注）
- 删除行数: 0（纯追加，无覆盖）
- 原有条目（Phase03 P0/P1/P2/P7-P12 各工单）完整保留
- 符合 NO_OVERWRITE 约束 ✅

## 五、约束合规 (7/7)

| # | 约束 | 状态 |
|:-:|------|:---:|
| 1 | BRANCH_LOCKED (feature/v88-g1) | ✅ |
| 2 | NO_OVERWRITE (0 删除，纯追加) | ✅ |
| 3 | NO_MODIFY_V87 (0 v87 文件触及) | ✅ |
| 4 | NO_EDIT_RELEASE_TAG (0 tag 操作) | ✅ |
| 5 | NO_ZHIJI_API_CALL (0 实际调用) | ✅ |
| 6 | NO_FACTOR_COMPUTE (0 因子计算) | ✅ |
| 7 | NO_ENGINE_MODIFY (0 引擎修改) | ✅ |

## 六、状态

- **ARBITER_ON_STANDBY_AWAIT_KEY_A**（维持）
- **KEY_A**: ABSENT
- **KEY_B**: ABSENT（不自动签发）
- **PHASE04_IGNITION**: FROZEN
- **VISUAL_ASSET_SEALED**: TRUE
- **DELIVERY_STATUS**: READY_FOR_DSHB_QC

---

*V88 Phase03 P14 | HERMEShf | asset_delivery_path v1.0 | 2026-10-17T21:21 +0800*
*零行情调用 / 零外部 API / 7 项约束全部合规*
