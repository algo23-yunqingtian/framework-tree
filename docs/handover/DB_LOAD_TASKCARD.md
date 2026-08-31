# 三表灌库 · 任务卡（给另一台服务器的 agent）

> 任务：把 `analysis/db/indicator_tree.db` 的**时序数据**灌满。元数据和灌库脚本已由主脑做好，你只需拉数。
> 读完本文档即可开工，无需翻旧会话。⚠️ 本文档第 2 节是**强制护栏**，上次有 agent 违反导致丢数据，务必遵守。

---

## 0. 任务边界（你做什么 / 不做什么）

| | 内容 |
|---|---|
| ✅ **你做** | 为五金属 (ZN/NI/SN/SI/LI) + 铜铝缺口的指标**拉取知几时序数据** → 写入 `framework-tree/scripts/api_cache.db` |
| ✅ **你做** | 拉完重跑 `python3 analysis/spec/db_load.py` 重建 `indicator_tree.db` |
| ✅ **你做** | 若你**不在本机**，按第 1.1 节导出 JSONL 回流（不能只写 .db —— `.gitignore` 第 1 行是 `*.db`，git 不跟踪） |
| ❌ **别碰** | `data/indicators_v1.json`（指标元数据，主脑独占，改=覆盖别人工作） |
| ❌ **别碰** | `data/tree_config.json`、`scripts/chart_kits.py`、`scripts/reclaim.py` |
| ❌ **别碰** | `analysis/spec/db_load.py`（灌库脚本，已验收；要改先问主脑） |
| ❌ **别做** | Step4 建页（那是另一个任务，走 task/* 分支） |

**一句话**：你的输出只有两个文件变——`scripts/api_cache.db`（拉数写入）和 `analysis/db/indicator_tree.db`（重跑脚本重建）。

---

## 1. 环境准备（开工前 5 分钟，必做）

```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
# ① 基线核验（关键！）
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
#   必须输出 786。若 < 786 → 你基线旧，必须先 rebase，否则重跑注册会丢数据（见第 2 节事故）

# ② 知几 API 可用性（配额已恢复，但仍需实测确认）
python3 ~/.hermes/scripts/zhiji_api.py search "锌 冶炼 产量"
python3 ~/.hermes/scripts/zhiji_api.py series FU00016362 2025-01-01 2026-08-31
#   两个都能返回真实数据（非 HTTP 429）才继续。若 429 → 停下来报主脑，不要反复重试

# ③ 当前数据底座（了解起点）
python3 -c "
import sqlite3, json
c=sqlite3.connect('scripts/api_cache.db').cursor()
print('api_cache.db 现有:', c.execute('SELECT code,COUNT(*) FROM indicator_cache GROUP BY code ORDER BY code').fetchall())
print('总计:', c.execute('SELECT COUNT(*) FROM indicator_cache').fetchone()[0], '行')
"
```

**当前起点**：`api_cache.db` 有 172 条（PB 77 / CU 43 / AL 52），**五金属 ZN/NI/SN/SI/LI 全为 0 条**。`indicators_v1.json` 共 786 个指标 key，其中仅 172 个已拉数据，**614 个待拉**。

### 1.1 数据回流通道（⚠️ 跨服务器必读）

**先判断你在这台机器上还是另一台机器**：

```bash
# 测试: 这个目录是否存在
ls /home/ubuntu/analysis/spec/db_load.py
```

| 情形 | 通道 |
|---|---|
| **文件存在**（同机器） | 直接写 `scripts/api_cache.db`，重跑 `db_load.py` 即完成。跳过本节。 |
| **文件不存在**（另一台机器） | ⚠️ **不能只写 .db**。`framework-tree/.gitignore` 第 1 行是 `*.db`，git **不跟踪任何 .db 文件**——你写的 api_cache.db 主脑永远看不到。必须按下方导出 JSONL。 |

#### 为什么不能只写 .db

```bash
# framework-tree/.gitignore 第 1 行
*.db
```

五金属待拉数据约 **34 万行**（daily 433 条 × ~730 点为主），压缩后每品种约 0.5-0.7MB，用 JSONL 提交 git 完全可行。

#### 导出命令（拉完数据后执行）

```bash
cd /home/ubuntu/framework-tree
python3 << 'PYEOF'
import sqlite3, json, os
from collections import defaultdict

# 从 indicator_tree.db 读 series（已重跑 db_load.py 的前提下）
conn = sqlite3.connect('/home/ubuntu/analysis/db/indicator_tree.db')
out_dir = 'data/db_export'
os.makedirs(out_dir, exist_ok=True)

# 五金属，按品种分文件
total_rows = 0
total_metrics = 0
for variety in ['ZN', 'NI', 'SN', 'SI', 'LI']:
    rows = conn.execute("""
        SELECT indicator_id, date, value
        FROM indicator_series
        WHERE indicator_id LIKE ?
        ORDER BY indicator_id, date DESC
    """, (f'%:{variety}',)).fetchall()
    if not rows:
        print(f'{variety}: 无数据，跳过')
        continue

    # 紧凑 JSONL: {"indicator_id":..., "date":..., "value":...}
    out_path = os.path.join(out_dir, f'series_{variety}.jsonl')
    with open(out_path, 'w') as f:
        for ind_id, date, value in rows:
            f.write(json.dumps({'indicator_id': ind_id, 'date': date, 'value': value},
                               ensure_ascii=False, separators=(',', ':')) + '\n')
    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f'{variety}: {len(rows):,} 行 -> {out_path} ({size_mb:.2f} MB)')
    total_rows += len(rows)
    total_metrics += len({r[0] for r in rows})

conn.close()
print(f'\n合计: {total_rows:,} 行, {total_metrics} 个指标')
PYEOF
```

> **重要**：导出到 `data/db_export/` 而不是 `scripts/`，因为 `data/` 目录没被 `.gitignore` 忽略（只忽略 `data/local_db/`）。JSONL 是 `.jsonl` 后缀，不受 `*.db` 规则影响。

#### 提交与推送

```bash
cd /home/ubuntu/framework-tree
git checkout -b task/db_load_5m
git add data/db_export/
git commit -m "[B-DBLOAD] 五金属时序数据导出: ZN/NI/SN/SI/LI"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin task/db_load_5m
```

> **禁止** `git add data/indicators_v1.json` 或其他 data/ 下文件——只 add `data/db_export/`。
> **禁止** 提交 `*.db` 文件（gitignore 会拦住，但 `git add -f` 会绕过，不要用）。

#### 主脑回收命令（你不用管，主脑做）

```bash
cd /home/ubuntu/framework-tree
git fetch origin
git checkout main
# 合并 JSONL 到本地 db
git checkout task/db_load_5m -- data/db_export/
python3 analysis/spec/db_import_jsonl.py data/db_export/   # 主脑提供的导入脚本
git checkout main -- data/db_export/    # 清掉本地 JSONL，避免污染 main
```

---

## 2. ⚠️ 强制护栏（上次有人违反，丢了 590 条数据）

**事故复盘**：2026-08-31，上一个 agent 基线停在 196 指标，直接基于旧基线重跑注册并 commit，**覆盖丢弃了主脑已推的 590 条五金属注册**（786→362）。主脑从 git 历史 `adc3c41` 抢救恢复（提交 `4d012a6`）。

| # | 护栏 | 违反后果 |
|---|---|---|
| 1 | **禁止修改 `data/indicators_v1.json`**。元数据已定稿 786 条，你的拉数写 `api_cache.db`，改 JSON = 覆盖主脑工作 | 丢数据（已发生过） |
| 2 | **禁止修改 `STATUS.md`**（主脑维护）。你只需在任务卡回报里报告进度 | hook 会拦截或污染真源 |
| 3 | **基线必须是 786**，开工前核验，<786 先 rebase | 旧基线注册 = 覆盖 |
| 4 | **禁止 `git checkout -f` / `git reset --hard` 到非 main 的 commit**。要干净工作区用 `git status` 检查 | 抹掉他人未提交改动 |
| 5 | **禁止直接 push main 做覆盖式提交**。若必须提交，走 `task/db_load` 分支 + PR | 覆盖风险 |
| 6 | **拉数必须 1 秒限频**，批量任务加断点续跑（勿一次性打满 API） | 触发 429 |
| 7 | 写任何文件前先 `git status -s` 确认工作区干净 | 混入他人改动 |

---

## 3. 数据表结构（已建好，理解即可，别改）

DB 位置：`analysis/db/indicator_tree.db`（线B 归属，**不推 GitHub**）

**表1 `indicator_meta`（元数据，836 行，全量指标 × 品种）**
| 字段 | 含义 |
|---|---|
| `indicator_id` | PK，格式 `key:variety`，如 `j21_close:PB` / `zn_311_output:ZN` |
| `key` | `indicators_v1.json` 的 key（统一 ID，**不造 IND 三段式**） |
| `variety` | ZN/CU/PB/AL/NI/SN/SI/LI/LC |
| `category` | price/supply/inventory/demand/trade/cost/balance（从 `_nodes` 节点号推导） |
| `node` | 节点号，如 `2.1` / `3.1.1` |
| `name_zh` / `unit` / `frequency` / `source` | 名称/单位/频率/来源 |
| `zhiji_id` | 知几指标 ID（拉数用这个） |
| `tier` | A/B（Step3 判定分层） |
| `has_series` | 0/1，series 表是否已有数据 |

**表2 `indicator_series`（时序，196,985 行）**
| 字段 | 含义 |
|---|---|
| `indicator_id` | FK → meta，格式同上 |
| `date` | `YYYY-MM-DD` |
| `value` | REAL |
| PK | `(indicator_id, date)` |

**当前状态**：meta 836 行（全量）/ series 196,985 行（172 个指标有数据，20.6%）。

**关键设计**：多品种指标（如 `主连` 的 ids 含 8 个品种）每个 `(key, variety)` 生成独立行，`indicator_id = key:variety` 保证 PK 唯一。你拉数后重跑脚本会自动展开。

---

## 4. 你的工作流程

### Step A：从 meta 表取待拉清单

```bash
python3 << 'PYEOF'
import sqlite3
c = sqlite3.connect('/home/ubuntu/analysis/db/indicator_tree.db').cursor()
# 取五金属待拉指标（zhiji_id 非空且无数据）
rows = c.execute("""
    SELECT indicator_id, key, variety, zhiji_id, name_zh, unit, frequency
    FROM indicator_meta
    WHERE variety IN ('ZN','NI','SN','SI','LI')
      AND has_series = 0
      AND zhiji_id IS NOT NULL AND zhiji_id != ''
    ORDER BY variety, key
""").fetchall()
print(f"五金属待拉: {len(rows)} 条")
import json
json.dump([dict(zip(['indicator_id','key','variety','zhiji_id','name_zh','unit','frequency'], r)) for r in rows],
          open('/home/ubuntu/analysis/iwencai/db_load_pending_5m.json','w'), ensure_ascii=False, indent=1)
print("清单已写:", '/home/ubuntu/analysis/iwencai/db_load_pending_5m.json')
PYEOF
```

> 约 621 条（五金属 590 注册 + 少量跨品种行）。zhiji_id 分两类：
> - **知几真 ID**（如 `FU00016362` / `a10098385` / `ID01000170` / `CM0000128429`）→ 用 `series` 命令拉
> - **kline 特殊 ID**（如 `kline:PB:D`）→ 6 条，需用 `kline` 命令而非 `series`，见下方坑位

### Step B：拉数写入 api_cache.db

参考现有脚本 `scripts/refresh_cache.py`（支持 i/j/cu_/al_ 前缀）和 `scripts/step3_fetch_data.py`（五金属 Step3 拉数版）。**注意两个坑**：

1. **1 秒限频**：zhiji_api.py 内置跨进程限频，但批量循环仍需自己控制节奏，勿并发打满
2. **断点续跑**：拉完 N 条立即写库，勿全部拉完才写（中断会丢全部进度）
3. **写 api_cache.db 的格式**（与现有 172 条一致）：
   ```python
   conn.execute("""
       INSERT OR REPLACE INTO indicator_cache
       (code, metric, zhiji_id, data_json, fetched_at, name, unit, freq)
       VALUES (?,?,?,?,?,?,?,?)
   """, (variety, key, zhiji_id, json.dumps(api_response), now, name, unit, freq))
   ```
   `data_json` 直接存 zhiji_api.py `series` 命令的**完整 JSON 响应**（含 `id/source/name/unit/freq/points`），`points` 是 `[{date, value}, ...]` 倒序（最新在前）。

### Step C：重跑灌库脚本重建 indicator_tree.db

```bash
cd /home/ubuntu && python3 analysis/spec/db_load.py
```

脚本会自动：备份旧库 → DROP+CREATE 两表 → 从 786 指标全量灌 meta → 从 api_cache.db 灌 series。跑完看输出报告。

### Step D：验收（见第 5 节）+ 回报主脑

---

## 5. 验收标准

```bash
python3 << 'PYEOF'
import sqlite3
c = sqlite3.connect('/home/ubuntu/analysis/db/indicator_tree.db').cursor()
meta = c.execute("SELECT COUNT(*) FROM indicator_meta").fetchone()[0]
series = c.execute("SELECT COUNT(*) FROM indicator_series").fetchone()[0]
has_data = c.execute("SELECT COUNT(*) FROM indicator_meta WHERE has_series=1").fetchone()[0]
orphan = c.execute("""SELECT COUNT(*) FROM indicator_series s
    WHERE NOT EXISTS (SELECT 1 FROM indicator_meta m WHERE m.indicator_id=s.indicator_id)""").fetchone()[0]
print(f"meta={meta} (应=836) | series={series} | 有数据={has_data} | 外键孤立={orphan} (应=0)")
# 五金属拉数进度
print("五金属按品种:")
for r in c.execute("""SELECT variety, COUNT(DISTINCT key) FROM indicator_meta
    WHERE variety IN ('ZN','NI','SN','SI','LI') AND has_series=1 GROUP BY variety"""):
    print(f"  {r[0]}: {r[1]} 条")
PYEOF
```

**通过条件**：外键孤立 = 0；五金属各品种 `has_series=1` 数量接近其 meta 行数（空数据指标除外，知几无序列属正常）。

---

## 6. 回报协议（做完告诉主脑）

在飞书回报以下四项，主脑据此验收：

1. 五金属各品种拉数成功/失败条数
2. `api_cache.db` 总行数变化（172 → ?）
3. 重跑 `db_load.py` 的完整输出报告
4. 失败指标清单（zhiji_id 无数据/429/其他），写入 `analysis/iwencai/db_load_fail_report.json`

**不要**改 STATUS.md 或 indicators_v1.json，主脑统一记录。

---

## 7. 坑速查

| 坑 | 解法 |
|---|---|
| `series` 命令对 `kline:XX:D` 形式的 zhiji_id 无效 | 这 6 条（主连/LME库存/SHFE库存/社库/TC/精炼产量）需用 `zhiji_api.py kline` 命令，或用其映射的 FU0001xxxx 真 ID |
| `series` 返回 `points` 为空 | 该 zhiji_id 无序列（知几无数据），属正常，记入失败清单别重试 |
| HTTP 429「总配额已用尽」 | 停手报主脑，勿反复重试污染缓存 |
| 中文关键词搜索返回杂项 | `search` 时关键词必须**空格分隔**（"锌 冶炼 产量" ✓，"锌冶炼产量" ✗） |
| api_cache.db 里 `metric` 字段必须 = `indicators_v1.json` 的 key | 写错 key，重跑 db_load.py 时 series 关联不上（has_series 恒为 0） |
| 日频数据最新点可能是未来日期 | 不用管，db_load.py 直接存原始 date |

---

## 8. 参考文件

| 文件 | 用途 |
|---|---|
| `analysis/spec/db_load.py` | 灌库脚本（已验收，含完整 DDL 和注释） |
| `analysis/spec/db_design.md` | 原始设计文档（2 表定义 + 查询模式） |
| `analysis/spec/HANDOVER_DB_LOAD_SPEC.md` | 本文档的框架设计决策版（背景/为什么这么做） |
| `scripts/refresh_cache.py` | 现有拉数脚本（i/j/cu_/al_ 前缀） |
| `scripts/step3_fetch_data.py` | 铜铝 Step3 拉数脚本（可参考五金属改造） |
| `scripts/api_cache.db` | 拉数目标库（172 行，不推 GitHub） |
| `~/.hermes/scripts/zhiji_api.py` | 知几 API 客户端 |
| `docs/AGENT_PARALLEL_PROTOCOL.md` | 并行协作协议（worktree 隔离） |
