#!/usr/bin/env bash
# =============================================================================
# V88 Phase03 P0 R3 自动化复测启动脚本
#
# TASK_ID : V88_PHASE03_P0_HERMES_GATE_RULE_UPDATE
# AGENT   : HERMEShf | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
#
# 职责（T3）：
#   DSHE 引擎适配（R-V88-030）完成后，一条命令完成全量 R3 权威复测：
#     ① 自动重建 phase03_test.db（DSHB 重建脚本，不入库 *.db —— R-V88-031）
#     ② 注入环境变量 V88_PHASE03_TEST_DB，拉起（适配版）NodeBindingEngine
#     ③ 执行 21 项主门禁 + 42 项阶段门禁（含 P0-11 DB 重建脚本可用性）
#     ④ 执行 24 项全链路回归套件，复核 A-3/B-3/C-3
#     ⑤ 输出双口径对照（口径A DB映射命中率 / 口径B 引擎真实渲染覆盖率）
#
# 约束合规：
#   BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG /
#   NO_ZHIJI_API_CALL（本脚本零知几 API 调用，全部离线） / APPEND_ONLY
#   *.db 不入库（AGENTS.md §7 红线）；生产库 scripts/api_cache.db 仅只读校验，绝不写入。
#
# 用法：
#   bash r3_auto_retest.sh                     # 全量复测（默认：重建 + 门禁 + 回归）
#   bash r3_auto_retest.sh --skip-rebuild      # 跳过重建（复用已有 phase03_test.db）
#   bash r3_auto_retest.sh --skip-regression   # 跳过回归套件（仅门禁）
#   bash r3_auto_retest.sh --tag <name>        # 输出文件标签（默认 r3_retest）
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../../.." && pwd)"
P0_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GATE_CHECKER="$SCRIPT_DIR/p0_gate_checker.py"
REGRESSION_SUITE="$SCRIPT_DIR/p0_full_regression_suite.py"
REBUILD_SCRIPT="$SCRIPT_DIR/import_all_to_testdb.py"
TESTDB="$P0_DIR/phase03_test.db"
TESTDB_DB_REL="analysis/e2e_output/v88/phase03/p0/phase03_test.db"
OUT_DIR="$P0_DIR"

SKIP_REBUILD=0
SKIP_REGRESSION=0
TAG="r3_retest"

for arg in "$@"; do
  case "$arg" in
    --skip-rebuild)     SKIP_REBUILD=1 ;;
    --skip-regression)  SKIP_REGRESSION=1 ;;
    --tag)              ;;   # 值在下一轮参数消费
    --*)                echo "❌ 未知参数: $arg"; exit 2 ;;
    *)                  TAG="$arg" ;;
  esac
done

cd "$REPO_ROOT"
echo "=============================================================================="
echo "V88 Phase03 P0 R3 自动化复测"
echo "TASK_ID : V88_PHASE03_P0_HERMES_GATE_RULE_UPDATE"
echo "AGENT   : HERMEShf | BRANCH: feature/v88-g1 (BRANCH_LOCKED)"
echo "REPO    : $REPO_ROOT"
echo "TAG     : $TAG"
echo "时间    : $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=============================================================================="

# 输出文件路径
GATE_OUT="$OUT_DIR/p0_${TAG}_gate_result.json"
REG_OUT="$SCRIPT_DIR/p0_${TAG}_regression_result.json"

# -----------------------------------------------------------------------------
# 0. 前置校验
# -----------------------------------------------------------------------------
echo ""
echo "[0/5] 前置校验"
FAIL=0

if [ ! -f "$GATE_CHECKER" ]; then
  echo "  ❌ 门禁脚本缺失: $GATE_CHECKER"; FAIL=1
fi
if [ ! -f "$REGRESSION_SUITE" ]; then
  echo "  ❌ 回归套件缺失: $REGRESSION_SUITE"; FAIL=1
fi
if [ ! -f "$REBUILD_SCRIPT" ]; then
  echo "  ❌ 重建脚本缺失: $REBUILD_SCRIPT"; FAIL=1
fi

# 引擎适配状态探测（R-V88-030 是否已处置）
ENGINE_SRC="$REPO_ROOT/scripts/node_binding_engine.py"
if grep -q "V88_PHASE03_TEST_DB" "$ENGINE_SRC" 2>/dev/null; then
  echo "  ✅ 引擎已适配 V88_PHASE03_TEST_DB 环境变量（R-V88-030 已处置）"
  ENGINE_READY=1
else
  echo "  ⚠️  引擎未适配 V88_PHASE03_TEST_DB（R-V88-030 未处置）"
  echo "      → 口径 B（引擎真实渲染覆盖率）预计仍为 0%，口径 A 将正常采集"
  ENGINE_READY=0
fi

if [ "$FAIL" -ne 0 ]; then
  echo "❌ 前置校验失败，终止"
  exit 2
fi

# -----------------------------------------------------------------------------
# 1. 重建 phase03_test.db（R-V88-031：不入库，运行时重建）
# -----------------------------------------------------------------------------
echo ""
echo "[1/5] 重建 phase03_test.db"
if [ "$SKIP_REBUILD" -eq 0 ]; then
  rm -f "$TESTDB"
  REBUILD_T0=$(date +%s)
  python3 "$REBUILD_SCRIPT" > "$OUT_DIR/p0_${TAG}_rebuild.log" 2>&1
  RB_EXIT=$?
  REBUILD_T1=$(date +%s)
  REBUILD_ELAPSED=$((REBUILD_T1 - REBUILD_T0))
  echo "  exit=$RB_EXIT  elapsed=${REBUILD_ELAPSED}s  log=p0_${TAG}_rebuild.log"
  if [ "$RB_EXIT" -ne 0 ]; then
    echo "❌ 重建失败（exit=$RB_EXIT），详见 $OUT_DIR/p0_${TAG}_rebuild.log"
    tail -15 "$OUT_DIR/p0_${TAG}_rebuild.log"
    exit 3
  fi
  if [ ! -f "$TESTDB" ]; then
    echo "❌ 重建完成但 phase03_test.db 未生成"
    exit 3
  fi
  DB_SIZE=$(stat -c%s "$TESTDB" 2>/dev/null || echo 0)
  echo "  ✅ 重建成功: $DB_SIZE 字节 (${REBUILD_ELAPSED}s, 阈值 <300s: $([ "$REBUILD_ELAPSED" -lt 300 ] && echo PASS || echo FAIL))"
elif [ -f "$TESTDB" ]; then
  echo "  ⏭  跳过重建（--skip-rebuild），复用现有: $(stat -c%s "$TESTDB") 字节"
  DB_SIZE=$(stat -c%s "$TESTDB")
else
  echo "❌ 无可用 phase03_test.db 且要求跳过重建"
  exit 3
fi

# -----------------------------------------------------------------------------
# 2. 注入环境变量
# -----------------------------------------------------------------------------
echo ""
echo "[2/5] 注入 V88_PHASE03_TEST_DB"
export V88_PHASE03_TEST_DB="$TESTDB"
echo "  V88_PHASE03_TEST_DB=$V88_PHASE03_TEST_DB"
echo "  （DSHE 适配版引擎与本门禁脚本共享同一环境变量）"

# -----------------------------------------------------------------------------
# 3. 门禁判定（21 主 + 42 阶段，含 P0-11 + 双口径）
# -----------------------------------------------------------------------------
echo ""
echo "[3/5] 门禁判定（R3 权威复跑 D-7）"
GATE_T0=$(date +%s)
python3 "$GATE_CHECKER" --json --save-baseline > "$GATE_OUT" 2>/dev/null
GATE_EXIT=$?
GATE_T1=$(date +%s)
echo "  exit=$GATE_EXIT  elapsed=$((GATE_T1-GATE_T0))s  out=$GATE_OUT"

python3 - "$GATE_OUT" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
print("  verdict      : %s" % d.get("verdict"))
print("  summary      : %s" % json.dumps(d.get("summary"), ensure_ascii=False))
d7 = d.get("d7_detail") or {}
print("  口径 B (引擎): %s%% (source=%s) 阈值60%% → %s" % (
    d7.get("real_coverage_pct"), json.dumps(d7.get("source_dist"), ensure_ascii=False),
    d7.get("p1_pass")))
dc = d.get("dual_caliber") or {}
print("  口径 A (DB)  : %s / %s = %s%% 阈值60%% → %s" % (
    dc.get("caliber_a_db_mapping_hit"), dc.get("caliber_a_db_mapping_denominator"),
    dc.get("caliber_a_db_mapping_hit_pct"), dc.get("caliber_a_pass")))
td = d.get("testdb_detail") or {}
print("  独立库       : %s 字节, %s 行, %s 指标, schema兼容=%s" % (
    td.get("testdb_size_bytes"), td.get("testdb_total_rows"),
    td.get("testdb_total_indicators"), td.get("schema_compatible")))
blocked = [r["gate_id"] for r in d.get("results", []) if r.get("status") == "BLOCKED_PRE_P0"]
failed  = [r["gate_id"] for r in d.get("results", []) if r.get("status") == "FAIL"]
print("  BLOCKED_PRE_P0: %s" % (blocked or "无"))
print("  FAIL          : %s" % (failed or "无"))
print("  主/阶段判定数 : %s / %s" % (d.get("main_gate_judged"), d.get("stage_gate_judged")))
PY

# -----------------------------------------------------------------------------
# 4. 全链路回归套件（24 用例）
# -----------------------------------------------------------------------------
echo ""
echo "[4/5] 全链路回归套件"
if [ "$SKIP_REGRESSION" -eq 0 ]; then
  python3 "$REGRESSION_SUITE" --json > "$REG_OUT" 2>/dev/null
  REG_EXIT=$?
  echo "  exit=$REG_EXIT  out=$REG_OUT"
  python3 - "$REG_OUT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("  用例数 : %s" % d.get("total_cases"))
print("  汇总   : %s" % json.dumps(d.get("summary"), ensure_ascii=False))
for c in d.get("cases", []):
    if c.get("status") in ("BLOCKED", "FAIL"):
        print("  %-10s %-32s %s" % (c.get("status"), str(c.get("name"))[:32],
                                   str(c.get("metric"))[:70]))
PY
else
  echo "  ⏭  跳过（--skip-regression）"
fi

# -----------------------------------------------------------------------------
# 5. 生产库零污染只读校验（R-09）
# -----------------------------------------------------------------------------
echo ""
echo "[5/5] 生产库零污染校验（scripts/api_cache.db 仅只读）"
python3 - <<'PY'
import sqlite3, os, time
p = "scripts/api_cache.db"
if os.path.exists(p):
    c = sqlite3.connect(p)
    rows = c.execute("SELECT COUNT(*) FROM indicator_cache").fetchone()[0]
    codes = [r[0] for r in c.execute("SELECT DISTINCT code FROM indicator_cache").fetchall()]
    c.close()
    print("  rows=%d  distinct_codes=%s  mtime=%s" % (
        rows, codes, time.strftime("%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))))
    ok = (rows == 3 and codes == ["AO"])
    print("  R-09 生产库零污染: %s" % ("✅ PASS" if ok else "❌ FAIL（基线应为 3 行 / code=AO）"))
else:
    print("  ⚠️  scripts/api_cache.db 不存在（本轮未触碰）")
PY

echo ""
echo "=============================================================================="
echo "R3 自动化复测完成 | tag=$TAG"
echo "  门禁结果 : $GATE_OUT"
echo "  回归结果 : $REG_OUT"
echo "  重建日志 : $OUT_DIR/p0_${TAG}_rebuild.log"
echo "=============================================================================="

# 退出码：门禁脚本自身判定（CONDITIONAL_PASS 视为 0）
exit $GATE_EXIT
