# 灌库·主脑 任务单（三表灌库回收）

> 你的角色：**灌库·主脑**（飞书另一个会话）。
> 分工：我（总控·主脑）负责指引方向 + 监督 + 门禁；你做三表灌库的回收执行。
> 目标：接收五金属 agent 拉回的数据，重建 `analysis/db/indicator_tree.db`，验收通过。
> 以下命令从头到尾照抄执行，产出与既有标准一致。

---

## 阶段 0：环境

```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# 必须 ≥ 786
bash scripts/bootstrap_agent.sh
```

## 阶段 1：等五金属 agent 拉数完成 + 合并 JSONL

五金属 agent 会在 `task/db_load_5m` 分支推 `data/db_export/series_{ZN,NI,SN,SI,LI}.jsonl`。
（如果你不是从他那里直接拿到文件，而是走 git：）

```bash
cd /home/ubuntu/framework-tree
git fetch origin
git checkout task/db_load_5m -- data/db_export/   # 把 JSONL 合并到本地
ls -lh data/db_export/                             # 确认 5 个 jsonl 存在
```

## 阶段 2：导入 JSONL 到 api_cache.db（灌数）

写一个导入脚本 `analysis/spec/db_import_jsonl.py`，把 JSONL 里的 `(indicator_id, date, value)` 还原成 `api_cache.db` 的 `indicator_cache` 行：

- `indicator_id` 格式是 `key:variety`（如 `zn_311_output:ZN`）→ 拆成 `key` + `code`
- 需要从 `indicators_v1.json` 查回该 key 的 `name/unit/freq`（若没有就留空）
- 用 `INSERT OR REPLACE` 写 `(code, metric, zhiji_id, data_json, fetched_at, name, unit, freq)`
- `data_json` 组装成 `{"id": zhiji_id, "name":..., "unit":..., "freq":..., "points":[{"date":..., "value":...}]}`（points 按 date 升序）
- 导入完打印：每个品种导入了多少行、多少指标

> 关键：**这是拉数回收的唯一通道**。五金属 agent 导出的 JSONL 就是他拉到的真实数据，导入后 `indicator_tree.db` 才能有完整时序。

## 阶段 3：重建 indicator_tree.db + 验收

```bash
cd /home/ubuntu
python3 analysis/spec/db_load.py
```

跑完看输出报告，然后独立验收：

```bash
python3 << 'PYEOF'
import sqlite3
c = sqlite3.connect('/home/ubuntu/analysis/db/indicator_tree.db').cursor()
meta = c.execute("SELECT COUNT(*) FROM indicator_meta").fetchone()[0]
series = c.execute("SELECT COUNT(*) FROM indicator_series").fetchone()[0]
has = c.execute("SELECT COUNT(*) FROM indicator_meta WHERE has_series=1").fetchone()[0]
orphan = c.execute("""SELECT COUNT(*) FROM indicator_series s
    WHERE NOT EXISTS (SELECT 1 FROM indicator_meta m WHERE m.indicator_id=s.indicator_id)""").fetchone()[0]
print(f"meta={meta} (应=836) | series={series} | 有数据={has} | 外键孤立={orphan} (应=0)")
for r in c.execute("""SELECT variety, COUNT(DISTINCT key) FROM indicator_meta
    WHERE variety IN ('ZN','NI','SN','SI','LI') AND has_series=1 GROUP BY variety"""):
    print(f"  {r[0]}: {r[1]} 条")
PYEOF
```

## 阶段 4：更新 STATUS.md + 回传

在 STATUS.md「近期变更记录」表格顶部插入一行（用 python 拆行，见 AGENTS.md 第 4 节）：

```
| 2026-08-31 | **[DB-LOAD] 三表灌库回收完成**（灌库·主脑） | 灌库·主脑 | 五金属拉数导入 + db_load.py 重建, meta=836 / series=xxx / 外键孤立 0 | 线B |
```

提交推送：
```bash
cd /home/ubuntu/framework-tree
git add STATUS.md && git commit -m "[DB-LOAD] 三表灌库回收"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

**回传**（发给总控·主脑）：
1. 每品种导入行数
2. db_load.py 完整输出
3. 验收四个数字（meta/series/有数据/外键孤立）
4. 失败清单（哪个品种哪些指标无数据）

## 红线

1. ❌ 不碰 `data/indicators_v1.json`（总控·主脑独占，改=覆盖 590 条）
2. ❌ 不碰 `chart_kits.py` / `reclaim.py`（总控·主脑独占）
3. ❌ 不 `git add -f` 提交 `*.db`
4. ✅ 验收必须「外键孤立=0」才回传
5. ✅ 有问题先问总控·主脑，别自己发明
