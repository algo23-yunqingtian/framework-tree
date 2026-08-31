# 五金属(锌/镍/锡/硅/锂) 拉数 + 建页 · 一键任务单

> 目标：为 ZN/NI/SN/SI/LI 五个品种完成「拉时序数据 + 建看板页面」。
> 指标元数据已全部就绪（786 条，五金属 590 条已注册），你只需做两件事：拉数 + 建页。
> 任务分 3 个阶段，每阶段结束回传一次，不要一口气做完不吭声。

---

## 阶段 0：环境（5 分钟）

```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# 必须 ≥ 786。少于 786 → 基线旧，rebase 后重试；仍不行就停下问主脑
bash scripts/bootstrap_agent.sh     # 上线自检，全绿才开工
```

---

## 阶段 1：拉时序数据（约 40 分钟，可后台跑）

把五金属 590 条注册指标的时序数据从知几拉下来，写入 `api_cache.db`。

```bash
cd /home/ubuntu/framework-tree
# ① 看这个脚本的用法
python3 scripts/step3_fetch_data.py --help
# ② 全量拉数（它自动筛 _origin 标记的 Step3 指标，含五金属）
python3 scripts/step3_fetch_data.py
# ③ 查看结果
cat analysis/iwencai/step3_fetch_report.json | head -30
```

要点：
- 脚本自动 **1.2s 限频**，590 条大约 40 分钟，建议 `nohup` 或后台跑，跑完再看报告
- **断点续跑**：脚本每次跑会跳过已验证的，中断后重跑即可续
- 成功 → 写入 api_cache.db 且 `verified=true`；失败 → 记录原因到 `step3_fetch_report.json`，**不要反复重试**，失败清单留在报告里

**阶段 1 回传**：成功/失败条数、失败原因分布（哪些是知几无序列）。

---

## 阶段 2：建页面（每节点 1-2 小时）

⚠️ **五金属没有现成建页引擎**（只有铜铝的 `build_cu_al_batch.py`）。你要**复制它做一个五金属版**：

```bash
cd /home/ubuntu/framework-tree
cp scripts/build_cu_al_batch.py scripts/build_5m_batch.py
# 修改 build_5m_batch.py：
# ① CODES/COLORS/THEMES 从 cu/al 改为 zn/ni/sn/si/li（颜色照 tree_config.json 各品种色）
# ② SECTION_NAME 保留（2价格/3供给/4库存/5需求/6进出口/7成本 通用）
# ③ chart cid 加品种前缀（echart_zn_21_c1），防跨品种串台
# ④ 只生成五金属节点：python3 build_5m_batch.py --zn-only 之类（仿 cu/al 的 --al-only）
```

然后按「节点 → 指标 → 建页 → 门禁」顺序逐品种做，**每品种做完就回传**，别攒着：

```bash
# 例：做锌板块2（价格信号，节点2.1-2.6）
python3 scripts/build_5m_batch.py 2.1 2.2 2.3 2.4 2.5 2.6 --zn-only
# 跑门禁
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py
```

**每节点流程**（对齐 AGENTS.md 3.5 规则）：
1. 用 `grep` 查该节点在 `indicators_v1.json` 里有哪些 `_nodes` 含此节点的指标（上一轮已注册 590 条，直接查）
2. 挑「1 正主 + 0~2 辅助」——正主必须贴合 `tree_config.json` 该节点 q 字段；已有页面用过的指标别当正主
3. 优先选 `api_cache.db` 里有数据的（阶段 1 已拉）；无数据的换别的或跳过并标注「待外部源」
4. 引擎生成 HTML → 门禁全绿 → 下一节点

**门禁改两处**（新页面要注册）：
- `check_html.py` 顶部 `PAGES` 列表加新页面
- `verify_render.js` 的 `PAGES` 加 `{key:'zn_21', file:'zn_2_1.html', seasonal:[cid...]}`，cid 从生成的 HTML 里抄

**阶段 2 回传（每品种一次）**：该品种建了几个节点/几个图、门禁结果、跳过节点及原因。

---

## 阶段 3：数据回流 + 最终回传

五金属数据量约 34 万行，`.db` 文件 git 不跟踪（`.gitignore` 第 1 行 `*.db`），**必须导出 JSONL 才能回传**：

```bash
cd /home/ubuntu/framework-tree
python3 << 'PYEOF'
import sqlite3, json, os
conn = sqlite3.connect('/home/ubuntu/analysis/db/indicator_tree.db')
out_dir = 'data/db_export'; os.makedirs(out_dir, exist_ok=True)
for v in ['ZN','NI','SN','SI','LI']:
    rows = conn.execute("SELECT indicator_id,date,value FROM indicator_series WHERE indicator_id LIKE ?",
                        (f'%:{v}',)).fetchall()
    with open(f'{out_dir}/series_{v}.jsonl','w') as f:
        for iid,d,val in rows:
            f.write(json.dumps({'indicator_id':iid,'date':d,'value':val},ensure_ascii=False,separators=(',',':'))+'\n')
    print(v, len(rows), '行')
PYEOF

git checkout -b task/db_load_5m
git add data/db_export/          # 只加这个目录！
git commit -m "[B-DBLOAD] 五金属时序数据导出"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin task/db_load_5m
```

⚠️ **只 `git add data/db_export/`**，绝不 `git add data/indicators_v1.json` 或其他 data/ 文件。

**最终回传**：
1. 各品种拉数成功/失败条数
2. 建页清单（品种 × 节点 × 图数）
3. 门禁三道全绿结果
4. 失败指标清单（无数据/429）
5. JSONL 导出的分支名 + 大小

---

## 红线（违反 = 丢数据，2026-08-31 刚出过事故）

1. ❌ 不碰 `data/indicators_v1.json`（主脑独占，你改了会覆盖 590 条注册）
2. ❌ 不碰 `chart_kits.py` / `reclaim.py` / `STATUS.md`（主脑独占）
3. ❌ 不 `git add -f` 提交 `*.db`
4. ❌ 不造数据：知几无序列的指标不上图，标「待外部源」
5. ❌ 不 `git checkout -f` / `git reset --hard`
6. ✅ 开工前基线必须 786，每品种建页完必须回传
