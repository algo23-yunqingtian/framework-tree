# V88 Phase03 P13 23 项资产全量哈希复核 (asset_gap_hash_check_P13.md)

> **TASK_ID**: V88_PHASE03_P13_HERMESHF_ASSET_INDEX_GAP_AUDIT
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **生成**: 2026-10-20
> **源 commit**: 8765c21
> **结果**: 23/23 核验完成, 无哈希漂移, 无换行漂移

## 一、复核范围与方法

| 项 | 值 |
|----|-----|
| 扫描目录 | web_asset/ + github_pages/ |
| 磁盘文件总数 | 23 |
| asset_index.lst 索引条目 | 22 |
| zip 包条目 (visual_asset_shturl.H.zip) | 29 (含 6 项非资产) |
| 比对维度 | MD5 + SHA256 + size + CRLF/CR 计数 + 只读权限 |
| 比对面 | 三方: 磁盘 / asset_index.lst / zip 内部 |

## 二、23 项资产全量哈希清单

| # | 路径 | 类型 | 字节 | MD5 | SHA256 | CRLF | 索引 | zip | 只读 |
|:-:|------|:---:|-----:|-----|--------|:---:|:---:|:---:|:---:|
| 1 | `github_pages/README.md` | MD | 2773 | `a94d67a255c64e2ea49caca4fc612c68` | `03ebbe7ae49738061b6e6d4f244e497e12af08bc27258ff620f93b52835d80eb` | 0 | 是 | 是 | 0444 |
| 2 | `github_pages/assets/01_kpi_cards.html` | HTML | 9046 | `13d534aacf12f068e690425c7c50bee1` | `79d0e89bda19b5e02a21fa2dd7a9c823705bff3695eaa53e9076a25ab19bd418` | 0 | 是 | 是 | 0444 |
| 3 | `github_pages/assets/01_kpi_cards.png` | PNG | 73713 | `c1a8b539e339b9971a7270a176a15b62` | `d5d59e8b41f7ae0643222bbc6200ac03ec11644b63614865b1d77f1d22c081d4` | 3 | 是 | 是 | 0444 |
| 4 | `github_pages/assets/02_factor_heatmap.html` | HTML | 8910 | `a7032a51cf24b5d7495039c2d1496697` | `2ac5363ba569512644510cac310074e3c206298392c57e3f0cbef4b162c21e74` | 0 | 是 | 是 | 0444 |
| 5 | `github_pages/assets/02_factor_heatmap.png` | PNG | 62523 | `a52233f179a18b171cbcc36d5ae2f703` | `1127e6d94efbf541022d76754f5cd2574aa4d26f526b465a8fabce38d1bdddf3` | 1 | 是 | 是 | 0444 |
| 6 | `github_pages/assets/03_scenario_bars.html` | HTML | 9677 | `9146b62be2d756416bfaaf0f208327b2` | `2c886c525907dff905569dbcf1265e4c088af6d50fa6b9c590dc0f4478d17aea` | 0 | 是 | 是 | 0444 |
| 7 | `github_pages/assets/03_scenario_bars.png` | PNG | 64814 | `8c270e3f780ec30ea28a3c3d704d50cc` | `ebeb58fcd2e35f085e1d1c7b5b2b22126ed8529422327dbdb51edd00ab955107` | 1 | 是 | 是 | 0444 |
| 8 | `github_pages/assets/04_risk_progress.html` | HTML | 10012 | `d1ecbe31a956e1c6bb0424daf586ac41` | `35252ba19bfa2a42714f67e4c0ee7d6262a9f29cc34b1930a382df7f426908c9` | 0 | 是 | 是 | 0444 |
| 9 | `github_pages/assets/04_risk_progress.png` | PNG | 80302 | `722f112b8d2ddc917d50268dd9877f90` | `f3aa388d81a5a3793e0a4c0ad9e266fc8fa712e6da81884711f96837d78ec903` | 1 | 是 | 是 | 0444 |
| 10 | `github_pages/assets/05_caliber_matrix.html` | HTML | 8987 | `5a63e1a27cf048876b64ad04b058ebb5` | `27df5a66cf1c0a92b39c3c71b893ce5dcd35440921754f70d92159d29c0f55cc` | 0 | 是 | 是 | 0444 |
| 11 | `github_pages/assets/05_caliber_matrix.png` | PNG | 66962 | `52006e66e2fc8f6fa3120d3e51686d77` | `5e0427b4599daa226a666d430e9ede1d30bdf5007723d9f1ef236728d5b6ca06` | 1 | 是 | 是 | 0444 |
| 12 | `github_pages/index.html` | HTML | 6093 | `280e8729f388fcab86266d3701d68939` | `3b3c4a27fca9381998c2f60762dba1c54b672a53d902cf177ebac652409b483a` | 0 | 是 | 是 | 0444 |
| 13 | `github_pages/wiki_admission_gate.md` | MD | 3591 | `3286e1469f7ce6b23bedfef061fbc63f` | `591ebeeb7692a07737462e12f58ed8440a17f444d291e470494f5d3ff5416b24` | 0 | **否** | 是 | 0444 |
| 14 | `web_asset/01_kpi_cards.html` | HTML | 9046 | `13d534aacf12f068e690425c7c50bee1` | `79d0e89bda19b5e02a21fa2dd7a9c823705bff3695eaa53e9076a25ab19bd418` | 0 | 是 | 是 | 0444 |
| 15 | `web_asset/01_kpi_cards.png` | PNG | 73713 | `c1a8b539e339b9971a7270a176a15b62` | `d5d59e8b41f7ae0643222bbc6200ac03ec11644b63614865b1d77f1d22c081d4` | 3 | 是 | 是 | 0444 |
| 16 | `web_asset/02_factor_heatmap.html` | HTML | 8910 | `a7032a51cf24b5d7495039c2d1496697` | `2ac5363ba569512644510cac310074e3c206298392c57e3f0cbef4b162c21e74` | 0 | 是 | 是 | 0444 |
| 17 | `web_asset/02_factor_heatmap.png` | PNG | 62523 | `a52233f179a18b171cbcc36d5ae2f703` | `1127e6d94efbf541022d76754f5cd2574aa4d26f526b465a8fabce38d1bdddf3` | 1 | 是 | 是 | 0444 |
| 18 | `web_asset/03_scenario_bars.html` | HTML | 9677 | `9146b62be2d756416bfaaf0f208327b2` | `2c886c525907dff905569dbcf1265e4c088af6d50fa6b9c590dc0f4478d17aea` | 0 | 是 | 是 | 0444 |
| 19 | `web_asset/03_scenario_bars.png` | PNG | 64814 | `8c270e3f780ec30ea28a3c3d704d50cc` | `ebeb58fcd2e35f085e1d1c7b5b2b22126ed8529422327dbdb51edd00ab955107` | 1 | 是 | 是 | 0444 |
| 20 | `web_asset/04_risk_progress.html` | HTML | 10012 | `d1ecbe31a956e1c6bb0424daf586ac41` | `35252ba19bfa2a42714f67e4c0ee7d6262a9f29cc34b1930a382df7f426908c9` | 0 | 是 | 是 | 0444 |
| 21 | `web_asset/04_risk_progress.png` | PNG | 80302 | `722f112b8d2ddc917d50268dd9877f90` | `f3aa388d81a5a3793e0a4c0ad9e266fc8fa712e6da81884711f96837d78ec903` | 1 | 是 | 是 | 0444 |
| 22 | `web_asset/05_caliber_matrix.html` | HTML | 8987 | `5a63e1a27cf048876b64ad04b058ebb5` | `27df5a66cf1c0a92b39c3c71b893ce5dcd35440921754f70d92159d29c0f55cc` | 0 | 是 | 是 | 0444 |
| 23 | `web_asset/05_caliber_matrix.png` | PNG | 66962 | `52006e66e2fc8f6fa3120d3e51686d77` | `5e0427b4599daa226a666d430e9ede1d30bdf5007723d9f1ef236728d5b6ca06` | 1 | 是 | 是 | 0444 |

## 三、三方比对结果

| 比对面 | 结果 |
|--------|:---:|
| 磁盘 22 项 vs asset_index.lst (MD5+size) | 22/22 一致 |
| 磁盘 23 项 vs zip 内部 (MD5) | 23/23 一致 |
| 索引外文件 | 1 (github_pages/wiki_admission_gate.md) |
| 只读权限覆盖 | 23/23 (0444) |

## 四、换行符核验 (回应工单"确认无文本换行哈希漂移")

| 项 | 值 |
|----|-----:|
| HTML/MD 文件数 | 13 |
| CRLF (0D0A) 总数 | 0 |
| 孤立 CR (0D) 总数 | 0 |
| PNG 文件数 | 10 (二进制, 未参与文本检测) |

**结论: 无文本换行哈希漂移。** 与 P12 结论一致 (P12 亦实测三方 0 个 CRLF)。

## 五、⚠️ 发现 1: 索引缺口 1 项

| 项 | 值 |
|----|-----|
| 文件 | `github_pages/wiki_admission_gate.md` |
| 磁盘存在 | 是 (3591B, md5=3286e1469f7ce6b23bedfef061fbc63f) |
| zip 内存在 | 是 (同名同哈希) |
| asset_index.lst 索引 | **否** |
| 只读权限 | 0444 (已锁定) |
| CRLF | 0 |

该文件三方一致 (磁盘 = zip), 哈希无漂移。缺口纯粹是**索引未收录**, 非内容异常。
处置方案见 `asset_index_solution_P13.md` (方案 A / 方案 B)。

## 六、发现 2: zip 内含 6 项非资产条目

visual_asset_shturl.H.zip 有 29 条目, 其中 23 项匹配挂载目录资产, **6 项在 zip 根目录,
不属于 web_asset/ 或 github_pages/**:

| # | zip 内条目 | 类型 | 字节 | MD5 |
|:-:|-----------|:---:|-----:|-----|
| 1 | `build_charts.py` | Python | 7766 | `459d0d2f4fd21e72ad20eeadba3a0aca` |
| 2 | `build_html_charts.py` | Python | 12198 | `29a062833f957804af49e6bdaf50d702` |
| 3 | `chart_lib.py` | Python | 14713 | `164419781ca20d8b9ed81b2dc8041adf` |
| 4 | `github_pages_deploy.zip` | 嵌套 zip | 314685 | `1bad4273f6f1f1823d6c930ca2f10f37` |
| 5 | `global_gate_dashboard_v9.md` | MD | 3705 | `79659fb73fd34329142e0a197fdc65bb` |
| 6 | `phase03_weekly_report.md` | MD | 4797 | `70f30e60a5491b30c7dad75ac56928be` |

**判定: 这 6 项不属于"22 项可视化资产"范畴**, 无需纳入 asset_index.lst。
它们是 P18 交付阶段的构建脚本与文档归档, 随交付包一同打包但非挂载资产。
**此 6 项不在缺口范围内**, 不影响索引完整性。

完整 SHA256 与字节数已在本节 MD5 列基础上可复算; 6 项未被任何封签锁定, 本轮不改动。

## 七、复核结论

- 23 项文件全部核验完成 (MD5 + SHA256 + size)
- 三方比对: 磁盘 vs 索引 22/22, 磁盘 vs zip 23/23, 全部一致
- **无文本换行哈希漂移** (CRLF=0, CR=0)
- **无二进制漂移** (PNG 10 项与 zip 内部一致)
- 只读权限 23/23 覆盖 (0444)
- 索引缺口 1 项 (方案见 asset_index_solution_P13.md)
- zip 额外 6 项非资产条目 (不在缺口范围, 不改动)
- **本轮未修改任何资产文件、未修改 asset_index.lst、未修改任何封签**

---

*V88 Phase03 P13 T0 | HERMEShf | 2026-10-20*
