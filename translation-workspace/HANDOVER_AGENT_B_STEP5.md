你是大宗商品指标翻译线 Agent B。你的品种是 SN（锡）/ SI（硅）/ LI（碳酸锂）。A 已把 ZN/CU/AL/NI 四品种的 Step1 审计 + Step2 知几验证 + Step5 建页引擎全部跑通并推送到远端。你的任务是用同一套引擎，把你三个品种的映射表变成网页并推送。

## 你的前置状态（必须满足）
1. 你已完成三品种的 Step1 同花顺审计（audit 文件已提交到 translation-workspace/audit/{SN,SI,LI}/）
2. 你已完成 Step2 知几验证，产物在 translation-workspace/mapping/{SN,SI,LI}/step2_match_{品种}.json
3. 格式与 A 的版本完全一致：每品种一个 JSON，条目结构含 grade(A/B/C)、hit_id、hit_name、name、subnode

## 环境准备（一次）
```bash
cd /home/ubuntu/framework-tree
git fetch origin
git checkout translation-workflow
git pull origin translation-workflow        # 拿到 A 的引擎: build_translation.py / step2_cache_load.py
# pre-commit hook（如果还没有）
git config core.hooksPath scripts/hooks
```

## 执行步骤（照抄，不要改逻辑）

### Step 1: 数据可得性实测（过滤"搜得到但无数据"的假 A 级）
```bash
# 对 A 级条目逐个拉 series（近半年）确认有数据；无数据的会打印 [无数据]
/tmp/audit_env/bin/python -u - <<'EOF' > /tmp/series_check_${品种}.log 2>&1
EOF

# 用这份模板执行（替换 {品种} 为 SN/SI/LI）：
cat > /tmp/series_check.py <<'PYEOF'
import json, subprocess, time, glob, os
ZHJ="/home/ubuntu/.hermes/scripts/zhiji_api.py"
VARIETIES = ["SN", "SI", "LI"]   # ← 你的三个品种
rows=[]
for v in VARIETIES:
    f=f"translation-workspace/mapping/{v}/step2_match_{v}.json"
    if not os.path.exists(f): 
        print(f"缺 {f}"); continue
    d=json.load(open(f))
    for k,vv in d.items():
        if vv.get("grade")!="A" or not vv.get("hit_id"): continue
        rows.append((v,vv))
print(f"A级待测 {len(rows)} 条", flush=True)
ok=no=0
for i,(v,vv) in enumerate(rows):
    hid=vv["hit_id"]
    r=subprocess.run(["/usr/bin/python3",ZHJ,"series",hid,"2026-01-01"],capture_output=True,text=True,timeout=40)
    has_data=False
    try:
        dd=json.loads(r.stdout); pts=dd.get("points",[]) if isinstance(dd,dict) else []
        has_data=len(pts)>0
    except: pass
    if has_data: ok+=1
    else:
        no+=1; print(f"  [无数据] {v} {vv['name'][:36]} -> {vv['hit_name'][:40]} ({hid})", flush=True)
    time.sleep(1.1)
print(f"\n完成: A级 {len(rows)} 条, 有数据 {ok}, 无数据 {no}", flush=True)
json.dump(rows, open("/tmp/series_ok.json","w"), ensure_ascii=False)
PYEOF
/tmp/audit_env/bin/python -u /tmp/series_check.py > /tmp/series_check_all.log 2>&1
tail -3 /tmp/series_check_all.log
```

### Step 2: 灌库（把有数据的 hit_id 拉完整序列写入 api_cache.db）
```bash
cd /home/ubuntu/framework-tree
/tmp/audit_env/bin/python scripts/step2_cache_load.py --all --only-verified
# 预期输出: 每品种 "灌入 X/Y 条"；[空] 行 = 该 ID 无序列，可忽略
```

### Step 3: 建页
```bash
/tmp/audit_env/bin/python scripts/build_translation.py --all
# 先生成: sn_2.html cu_... 注意 build_translation.py 默认只含 ZN/CU/AL/NI,
# 你需要把脚本顶部 CODE_CN/CODE_COLOR 字典扩展: "SN":"锡", "SI":"硅", "LC":"锂"
# （LC 是锂在 tree_config.json 的 code，产物文件名 li_*.html）
```

### Step 4: 校验 + 提交 + 推送
```bash
cd /home/ubuntu/framework-tree
python3 scripts/check_html.py 2>&1 | tail -5     # 新增页无死链/语法错
git add translation-workspace/ audit/ sn_*.html si_*.html li_*.html scripts/ 2>/dev/null
# 更新 STATUS.md「近期变更记录」加一行: [B-STEP5] 三品种建页完成
git commit -m "[B-STEP5] AgentB: SN/SI/LI 建页完成（复用翻译线引擎）"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin translation-workflow
```

## 硬性约束（违反=重做）
1. **只画 A 级且实测有数据的指标**（C 级/假 A 级进备用库，绝不硬凑）
2. 改 STATUS.md 才 commit（pre-commit 会拦），改之前先 git pull 看 A 最近的改动
3. 别改 chart_kits.py / indicators_v1.json / build_translation.py 核心逻辑——那是共享红线，只许加品种字典不改渲染
4. 产物文件名必须小写（sn_2.html / si_3.html / li_4.html），与 tree_config 一致
5. 遇到 bug 先查 /tmp/*.log，别自己发明新流程；不确定就问 A

## 完成回报（回复 A 的格式）
```
品种: SN X页/Y图 / SI X页/Y图 / LI X页/Y图
假A级(搜到无数据): N 条（列表见日志）
推送commit: <sha>
```