#!/bin/bash
# framework-tree 新 agent 上线自检（2026-08-31 主脑设计）
# 目的：把 AGENTS.md 里「必做事项」固化成一条命令，防止 agent 漏跑。
# 用法：cd /home/ubuntu/framework-tree && bash scripts/bootstrap_agent.sh
# 通过 = 输出绿色「✅ 可以开工」，异常 = 红色阻断项，修完再开工。

cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"
FAIL=0
WARN=0

echo "══════════════ framework-tree 上线自检 ══════════════"
echo "工作目录: $ROOT"

# ── 1. git 状态 ──────────────────────────────────────────
echo ""
echo "── [1/6] git 基线 ──"
if [ -n "$(git status -s)" ]; then
  echo "  ❌ 工作区有未提交改动，禁止开工（会覆盖/丢失）:"
  git status -s | sed 's/^/      /'
  FAIL=1
else
  echo "  ✅ 工作区干净"
fi
git fetch -q origin 2>/dev/null
LOCAL=$(git rev-parse HEAD); REMOTE=$(git rev-parse origin/main 2>/dev/null)
if [ "$LOCAL" = "$REMOTE" ]; then
  echo "  ✅ HEAD=origin/main ($(echo $LOCAL | cut -c1-7))"
else
  echo "  ❌ HEAD($(echo $LOCAL | cut -c1-7)) ≠ origin/main($(echo $REMOTE | cut -c1-7))"
  echo "     必须: git fetch && git rebase origin/main（基线旧会导致指标/页面缺漏）"
  FAIL=1
fi

# ── 2. pre-commit hook ──────────────────────────────────
echo ""
echo "── [2/6] 协作 hook（改产物必须写 STATUS.md）──"
HP=$(git config core.hooksPath)
if [ "$HP" = "scripts/hooks" ] && [ -f "scripts/hooks/pre-commit" ]; then
  echo "  ✅ hook 已安装 ($HP)"
else
  echo "  ⚠️ hook 未安装，执行安装: git config core.hooksPath scripts/hooks"
  git config core.hooksPath scripts/hooks && echo "  ✅ 已安装"
fi

# ── 3. 指标基线 ─────────────────────────────────────────
echo ""
echo "── [3/6] 指标基线 ──"
N=$(python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']))" 2>/dev/null)
V=$(python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(d.get('version'))" 2>/dev/null)
echo "  ℹ️  指标 $N 条 / version $V（以 STATUS.md 最新记载为准，当前应=196/3.42）"

# ── 4. 门禁基线（只跑 check_html，快）──────────────────
echo ""
echo "── [4/6] 门禁快检（check_html）──"
if python3 scripts/check_html.py >/tmp/_bootstrap_check.log 2>&1; then
  echo "  ✅ check_html 全 PASS"
else
  echo "  ❌ check_html FAIL（见 /tmp/_bootstrap_check.log），基线不绿禁止开工"
  FAIL=1
fi

# ── 5. 死链检查 ─────────────────────────────────────────
echo ""
echo "── [5/6] 死链 ──"
DL=$(python3 -c "
import re,glob,os
t=[x for f in glob.glob('*.html') for x in re.findall(r'href=\"([^\"]+\.html)\"',open(f,encoding='utf-8').read()) if not os.path.exists(x.split('#')[0])]
print(len(t))" 2>/dev/null)
if [ "$DL" = "0" ]; then
  echo "  ✅ 死链 0"
else
  echo "  ❌ 死链 $DL 个，先清再开工"
  FAIL=1
fi

# ── 6. 知几配额 ────────────────────────────────────────
echo ""
echo "── [6/6] 数据源可用性 ──"
# 2026-08-31 修：原探测词"测试 配额"含"配额"，zhiji_api.py 会原样回显 query 字段，
# grep "429\|配额" 必然自命中 → API 正常时也永久假阳性报配额耗尽。
# 改法：探测词换无触发词，改判 "error" 字段 / HTTP 状态码。
Q=$(python3 ~/.hermes/scripts/zhiji_api.py search "锌 社会库存" 2>&1 | head -1)
if echo "$Q" | grep -qE '"error"|HTTP 429'; then
  echo "  ⚠️ 知几 API 不可用（$(echo "$Q" | grep -o 'HTTP [0-9]*' | head -1)）→ 数据拉取/复核任务阻塞"
  WARN=1
else
  echo "  ✅ 知几 API 可用"
fi

# ── 汇总 ────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════"
if [ "$FAIL" = "1" ]; then
  echo "  🔴 存在阻断项，修复后再开工（红色 ❌ 项）"
  exit 1
else
  echo "  ✅ 可以开工"
  [ "$WARN" = "1" ] && echo "  ⚠️ 有警告项：知几配额耗尽，数据任务等待主脑指示"
fi
echo "══════════════════════════════════════════════════"
