#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 dshe_alias_integrate_test 目录的文件 MD5 清单 + 追加 V85_ALL_ANALYSIS_COMPLETE 到 JOB_READY.flag。
只读上游真源；仅写本目录内产物与 v85/JOB_READY.flag。
"""
import hashlib, os, datetime

DIR = os.path.dirname(os.path.abspath(__file__))
V85 = os.path.dirname(DIR)
OUT_CSV = os.path.join(DIR, "output_file_md5.csv")
FLAG = os.path.join(V85, "JOB_READY.flag")

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()

skip = {"__pycache__", "output_file_md5.csv"}
rows = []
for f in sorted(os.listdir(DIR)):
    if f in skip:
        continue
    p = os.path.join(DIR, f)
    if os.path.isdir(p):
        continue
    rows.append((f, os.path.getsize(p), md5(p)))

header = ["file", "bytes", "md5"]
with open(OUT_CSV, "w", encoding="utf-8", newline="") as w:
    w.write(",".join(header) + "\n")
    for f, n, m in rows:
        w.write("%s,%d,%s\n" % (f, n, m))

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print("== 文件清单 (%d 个) ==" % len(rows))
for f, n, m in rows:
    print("%-42s %9d  %s" % (f, n, m))

flag_lines = [
    "",
    "# ============================================================ #",
    "# V85_ALL_ANALYSIS_COMPLETE %s" % now,
    "# task       : DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY",
    "# branch     : feature/v85-chart-template",
    "# output_dir : analysis/e2e_output/v85/dshe_alias_integrate_test/",
    "# md5_list   : dshe_alias_integrate_test/output_file_md5.csv (%d files)" % len(rows),
    "# deliverables:",
    "#   alias_blacklist_combine_eval.md      别名库+联合黑名单(31)回放评估 41+200+1134",
    "#   ths_missing_alias.csv                THS别名覆盖专项 2359行 (MISSING=0)",
    "#   alias_lib_import_validate.py         导入链路校验 V1-V9 可运行",
    "#   alias_import_validation_report.md    import_ready=FALSE (BLOCK1/WARN2/INFO1)",
    "#   ambiguous_indicator_rerated.csv      歧义448行二次复核重分级",
    "#   alias_lib_v86_roadmap.md             V86迭代路线 10批次 16.25-24.25人天",
    "#   alias_lib_v85_final_quality_report.md 最终质量报告",
    "# key_metrics : Recall=100.00% Precision=22.65% Specificity=42.86% F1=36.94% BA=71.43%",
    "# key_finding : 6条DSH-B扩展黑名单规则零边际贡献 (delta=0); 注入机制已验证生效 (2/6探针门禁移动)",
    "# caveat      : semantic_blacklist_v85_final.json 与 full_488_template_playback_result.csv 缺失, 已用代理替代",
    "V85_ALL_ANALYSIS_COMPLETE=TRUE",
    "# ============================================================ #",
    "",
]
with open(FLAG, "ab") as f:
    f.write("\n".join(flag_lines).encode("gbk", errors="replace"))

print("\n已写出: %s (%d 行)" % (OUT_CSV, len(rows)))
print("已追加: %s" % FLAG)
print("V85_ALL_ANALYSIS_COMPLETE=TRUE")
