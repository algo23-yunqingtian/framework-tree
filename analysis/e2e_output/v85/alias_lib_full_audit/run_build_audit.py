# -*- coding: utf-8 -*-
"""
run_build_audit.py  — 审计执行包装器
=====================================
DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST

作用: 原样加载 alias_match_presearch/build_alias_library.py 的全部构建逻辑,
      仅把其输出目录常量 OUT 重定向到本审计目录, 保证:
        (1) 原脚本一个字节都不改 (T4.2 只读约束)
        (2) 全部产物落到 alias_lib_full_audit/ 下 (T4.4 只新增不覆盖)
        (3) 全部统计数字来自本次真实运行, 不读取旧 _stats.json

实现: 读取原脚本源码 -> 用正则替换 OUT 常量 -> 在独立命名空间中 exec。
exec 之后的行为与原脚本完全一致 (同一份逻辑代码), 差异仅为输出路径。

用法: python run_build_audit.py
      运行日志由调用方用 PowerShell 重定向捕获, 便于逐行审计。
"""
import re, sys, os, hashlib
from datetime import datetime, timezone, timedelta

REPO = r"D:\DSH_WORK\framework-tree"
PRESEARCH = REPO + r"\analysis\e2e_output\v85\alias_match_presearch"
AUDIT = REPO + r"\analysis\e2e_output\v85\alias_lib_full_audit"
SRC = PRESEARCH + r"\build_alias_library.py"

os.makedirs(AUDIT, exist_ok=True)

src_bytes = open(SRC, "rb").read()
src = src_bytes.decode("utf-8")
src_md5 = hashlib.md5(src_bytes).hexdigest()
src_sha256 = hashlib.sha256(src_bytes).hexdigest()

# 仅替换输出目录常量。保持逻辑代码逐字节不变。
# 注意: re.subn 的 replacement 字符串会处理反斜杠转义, 因此用 lambda 返回字面量。
pattern = re.compile(r'(?m)^OUT = V85 \+ r"\\alias_match_presearch"$')
new_src, n = pattern.subn(lambda _m: 'OUT = V85 + r"\\alias_lib_full_audit"', src)
assert n == 1, "OUT 常量未命中, 原脚本结构已变化, 拒绝执行"

# 同时把 TASK 常量换成审计任务号, 便于产物溯源
new_src, n2 = re.subn(
    r'(?m)^TASK = "DSHE-B_V85_INDICATOR_ALIAS_LIB_AND_FUZZY_MATCH_PRESEARCH"$',
    'TASK = "DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST"',
    new_src,
)
assert n2 == 1, "TASK 常量未命中"

print("=" * 74)
print("审计执行包装器 run_build_audit.py")
print("  执行时间(UTC+8): %s" % datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"))
print("  源脚本 : %s" % SRC)
print("  源脚本大小: %d 字节 | MD5 %s | SHA256 %s" % (len(src_bytes), src_md5, src_sha256))
print("  替换   : OUT -> alias_lib_full_audit (1 处) | TASK -> 审计任务号 (1 处)")
print("  其余代码: 逐字节未修改")
print("  输入源 : 全部为只读原始文件, 不读取 alias_match_presearch/_stats.json")
print("=" * 74)
print()

ns = {"__name__": "__main__", "__file__": SRC}
exec(compile(new_src, SRC, "exec"), ns)

print()
print("=" * 74)
print("审计执行完成。全部统计数字均来自本次运行 (源脚本 MD5 %s)。" % src_md5)
print("=" * 74)
