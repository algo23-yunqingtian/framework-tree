#!/usr/bin/env python3
"""
V88 Phase03 P1 — 派生指标静默回退陷阱防护单元测试
TEST_ID: test_derive_indicators_guard
"""
import sqlite3, os, sys, subprocess

REPO = "/home/ubuntu/framework-tree"
DERIVE_SCRIPT = os.path.join(REPO, "analysis/e2e_output/v88/phase03/p1/scripts/derive_indicators.py")
R3_SCRIPT = os.path.join(REPO, "analysis/e2e_output/v88/phase03/p0/scripts/r3_auto_retest.sh")

def test_derive_script_exists():
    assert os.path.exists(DERIVE_SCRIPT), f"派生脚本不存在: {DERIVE_SCRIPT}"
    print("  ✅ test_derive_script_exists PASS")

def test_derive_accepts_db_param():
    with open(DERIVE_SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    assert "--db" in src or "argparse" in src, "派生脚本不接受 --db 参数"
    print("  ✅ test_derive_accepts_db_param PASS")

def test_r3_script_has_1b_module():
    with open(R3_SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    assert "[1b]" in src, "r3_auto_retest.sh 缺少 [1b] 模块"
    assert "derive_indicators.py" in src, "r3_auto_retest.sh 未调用派生脚本"
    assert "exit 3" in src, "r3_auto_retest.sh 缺少 exit 3 硬阻断"
    print("  ✅ test_r3_script_has_1b_module PASS")

def test_r3_script_has_db_size_check():
    with open(R3_SCRIPT, "r", encoding="utf-8") as f:
        src = f.read()
    assert "DERIVE_ROWS" in src, "r3_auto_retest.sh 缺少库规模校验变量"
    assert "distinct_codes" in src, "r3_auto_retest.sh 缺少 distinct_codes 校验"
    print("  ✅ test_r3_script_has_db_size_check PASS")

def test_derive_prevents_regression():
    """验证派生重建后库指标数 > 615"""
    testdb = os.path.join(REPO, "analysis/e2e_output/v88/phase03/p0/phase03_test.db")
    if os.path.exists(testdb):
        c = sqlite3.connect(testdb)
        try:
            inds = c.execute("SELECT COUNT(DISTINCT code) FROM indicator_cache").fetchone()[0]
            assert inds > 615, f"库指标数 {inds} ≤ 615，处于回退状态"
            print(f"  ✅ test_derive_prevents_regression PASS (指标数={inds})")
        finally:
            c.close()
    else:
        print("  ⏭ test_derive_prevents_regression SKIP (库不存在)")

if __name__ == "__main__":
    print("V88 Phase03 P1 — 派生指标防护单元测试")
    print("=" * 50)
    test_derive_script_exists()
    test_derive_accepts_db_param()
    test_r3_script_has_1b_module()
    test_r3_script_has_db_size_check()
    test_derive_prevents_regression()
    print("=" * 50)
    print("全部 PASS")
