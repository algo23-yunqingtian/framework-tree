# framework-tree 跨服务器协作交接指南（协作手册 Playbook）

> 版本：v1.0 · 2026-08-29
> 读者：**另一台服务器上的全新 agent**（无任何历史上下文）
> 目标：拿到本文档即可独立跑通完整生产流水线，并按统一格式回传给主脑

**一句话定位**：本项目是「有色金属产业指标树看板」，8 品种（铜/铝/铅/锌/镍/锡/锂/硅），数据来自 Zhiji（知几）API，前端是 Dark ECharts 高密度静态页，GitHub Pages 直接部署。

---

## 一、5 分钟上手

```bash
# 1. 拉代码
git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree

# 2. 装依赖（Python 3.11+ / Node 18+）
pip install requests
npm install jsdom --prefix /tmp        # verify_render.js 用

# 3. 放好知几 API 客户端（主脑位置，可复制）
mkdir -p ~/.hermes/scripts
# 把 zhiji_api.py 放到 ~/.hermes/scripts/（内含 3 个 key，见第七章）

# 4. 首次拉数据入库
python3 scripts/refresh_cache.py

# 5. 重建页面
for f in scripts/build_pb_*.py; do python3 "$f"; done

# 6. 跑门禁（必须全绿）
python3 scripts/check_html.py
node scripts/verify_render.js

# 7. 推送上线
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
sleep 75    # GitHub Pages 构建延迟

# 8. 验收
curl -sI "https://algo23-yunqingtian.github.io/framework-tree/pb_23_overseas_price.html" | head -1
```

**两个地址别搞混**：
- 源码仓库：`https://github.com/algo23-yunqingtian/framework-tree`（只有 .html 文件名，看不到渲染效果）
- 线上看板：`https://algo23-yunqingtian.github.io/framework-tree/`（这个才是给用户看的）

---

## 二、架构全景

```
【数据层】
 Zhiji API（观=行情K线 / 讯=新闻 / 料=大宗指标）
     │  refresh_cache.py（1秒限频，INSERT OR REPLACE）
     ▼
 api_cache.db（SQLite，本地，不推 GitHub）
     │
【元数据层】
 data/indicators_v1.json ← 唯一真源（指标ID/名称/单位/频率/zhiji_id/是否验证）
     │
【生成层】
 scripts/chart_kits.py ← 公共图表模块（371行，核心）
 scripts/build_pb_XX.py ← 每个子页一个 build 脚本（只写"读哪个指标+画哪张图+备注"）
     │  生成
     ▼
 pb_XX.html（静态页，含真实数据内联，Dark ECharts）
     │
【校验层】
 scripts/check_html.py     ← 静态校验（文件/字节/图表数/备注数/公共JS/季节函数）
 scripts/verify_render.js  ← jsdom+ECharts mock 真实渲染校验
     │
【发布层】
 git push origin main → GitHub Pages 自动构建（60-90秒）
     │
【状态层】
 STATUS.md ← 全局状态唯一真源，每次改动必须 commit+push
```

**两条线隔离**（`COLLABORATION.md` 已定义，务必遵守）：

| | 线A：架构+前端 | 线B：指标+数据 |
|---|---|---|
| 任务 | 前端页面/目录树/API/ECharts/GitHub | 同花顺Prompt/指标清单/zhiji_id验证/入库 |
| 写权限 | `/home/ubuntu/framework-tree/` | `/home/ubuntu/analysis/iwencai/` |
| 禁止写 | `analysis/iwencai/` | `framework-tree/` |

隔离由 `~/.hermes/scripts/file_write_lock.py` 白名单强制，串线写入会被拒。

---

## 三、7 步生产流水线（核心）

新增一个子节点（例如「铅 2.7 加工费」）的完整流程：

### Step 1 同花顺发散 → 图表方案（人工环节，5-10 分钟）

这是**唯一无法自动化**的环节，必须人工在浏览器操作 `www.iwencai.com`：
- 入口：左侧「新对话」→ 底部 `[contenteditable].ql-editor` 粘贴 prompt → `.send-button` 点击
- Prompt 模板：`prompt_lib/template_v19.md`（v18/v19 通用题材精准枚举器·复合图设计师）
- **逐节点发，不要一次发 4 个节点**：实测一次 4 节点出 7 图 vs 逐节点 18 图，后者能主动排除误入指标并带 HS 编码+真实月度数据
- 返回后落盘，格式见第四章 (a)

### Step 2 知几验证 → 确认 zhiji_id

```bash
# search：找指标ID（中文关键词之间必须用空格分隔，否则分词误命中）
python3 ~/.hermes/scripts/zhiji_api.py search "新加坡 铅 仓单"
# ✅ 精准命中 FU00023414 LME铅注册仓单新加坡
# ❌ 写成"新加坡铅仓单"（无空格）会返回钴/铝/锡

# series：拉时序（返回 points 倒序，最新在前）
python3 ~/.hermes/scripts/zhiji_api.py series a10193708 2015-01-01 2026-08-29
```

**命中阈值**：score≥12 = A 命中；6-11 = B 弱匹配；<6 = C 未命中。
**必须人工审核**：滑动窗口分词会把"铅锭"误配到"镁锭"、"铅"误配到"铜/镍/锌"。逐条检查 name 前缀是否为正确品种名。

### Step 3 注册到 indicators_v1.json

在 `indicators` 下新增条目（格式见第四章 b）：

```json
"j27_tc": {
  "name": "铅精矿加工费",
  "unit": "美元/干吨",
  "freq": "weekly",
  "verified": true,
  "ids": {"PB": "a10xxxxxxxx"},
  "category": "price",
  "subleaf": "2.7加工费",
  "source": "SMM"
}
```

同时更新顶层 `version`（如 2.4 → 2.5）、`updated`、`change`。

### Step 4 拉数入库

```bash
python3 scripts/refresh_cache.py --metrics j27_tc
# 读 indicators_v1.json → 取 verified=true 的条目 → 逐个拉取 → 写 api_cache.db → 1秒限频
```

### Step 5 Build 生成页面

新建 `scripts/build_pb_27.py`，只写三件事（照抄 `build_pb_23.py` 结构）：

```python
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html)

CIDS = ["echart_27_c1", "echart_27_c2", "echart_27_c3"]

m1 = load_metric("j27_tc")          # 1. 读哪个指标
d1 = pairs(m1)

h1, j1 = chart_dual(                 # 2. 画哪张图
    "echart_27_c1", "标题", "副标题",
    d1, "#b06a32", "系列名", "单位",
    [], "#5b98c9", "系列名", "单位",
    "什么时候看：…<br>怎么看：…"      # 图备注
)

html = page_html("铅(PB) 2.7", "...", "...", h1, h2, h3, NOTE, "页脚", j1, CIDS)
write_html("pb_27_price.html", html)
```

**chart_kits 公共 API**：

| 函数 | 用途 |
|---|---|
| `load_metric(mid, code="PB")` | 从 api_cache.db 读时序 → `{name,unit,freq,n,points,dates,values}` |
| `pairs(m)` | → `[[date, value], ...]` |
| `latest(m)` | → 最新日期字符串 |
| `sub_series(m_a, m_b, na, nb)` | 两条序列差值（按共有日期） |
| `_detect_gran(data)` | 自动检测粒度 `'D'`日度 / `'M'`月度 |
| `chart_line_t(cid, title, sub, color, data, note, default_seasonal=False)` | 单指标 时序⇄季节 双模式 |
| `chart_dual(...)` | 双轴复合图 |
| `chart_triple(...)` | 三系列堆叠面积图 |
| `page_html(title, hcrumbs, hright, h1, h2, h3, note_html, footer, js_body, cids)` | 拼装页面 |
| `write_html(filename, html)` | 输出到仓库根目录 |

### Step 6 跑门禁（必须全绿）

```bash
python3 scripts/check_html.py       # 需先在 PAGES 配置里加你的页
node scripts/verify_render.js       # 需在 PAGES 里加 {key, file, seasonal:[cids]}
```

两道门禁检查项：
- `check_html.py`：文件存在/字节区间/图表容器数/chart-note数/cid已初始化/公共JS完整/季节函数/echarts引用/版本号
- `verify_render.js`：jsdom 加载真实 HTML + ECharts mock，真实调用 `__seasonalizeBy*`/`__tgl`，验证季节按钮切换产出历年 series

### Step 7 推送上线

```bash
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
sleep 75
curl -s --max-time 20 -o /dev/null -w "%{http_code} %{size_download}\n" \
  "https://algo23-yunqingtian.github.io/framework-tree/pb_27_price.html"
```

最后更新 `STATUS.md` 并 commit+push（30 秒内必须推，用 python 拆行写入，见坑 6）。


---

## 四、格式契约（Schema Contract）⭐ 核心章节

这一章解决「两边格式必须一致」的问题。**所有产物必须严格按下述格式，不得自行发挥。**

### (a) 同花顺发散记录

| 项 | 约定 |
|---|---|
| 目录 | `analysis/iwencai/<品种大写>/<板块编号>_<英文短名>_<YYYYMMDD>.md` |
| 示例 | `analysis/iwencai/PB/2x_diversify_20260829.md` |
| 编码 | UTF-8 |

**文件头固定 4 行**（必填，主脑靠这个识别批次）：

```markdown
# 同花顺发散 · <品种> <板块> · <YYYYMMDD>
prompt: template_v19  # 用的哪个 prompt 模板
节点数: <N>           # 发了几个节点
状态: 待审核 | 已定稿 | 已入库
```

**每个节点固定结构**：

```markdown
#### <编号> <节点名>（如 2.1 盘面结构）

**发散返回（原始，勿改）**：
<粘贴同花顺返回全文>

**自检**：
- 图数: N（建议 3 图/节点）
- 越界指标（价格/价差误入库存页等）: <列名或删除>
- 需排除: <列名>

**定稿图表**：
| 图 | 标题 | 数据源 | zhiji_id | 待验证 |
|---|---|---|---|---|
| 1 | ... | 观 kline | — | 待查 |
```

### (b) 指标入库产物

**① `data/indicators_v1.json` 条目格式**（唯一真源，务必严格）：

```json
"<id>": {
  "name": "<指标中文名>",
  "unit": "<单位>",
  "freq": "daily|weekly|monthly",
  "verified": true,
  "ids": { "<品种码>": "<zhiji_id>" },
  "category": "price|supply|inventory|demand|trade|cost|balance",
  "subleaf": "<编号><名称>",
  "source": "<数据来源 LME/SMM/海关/上期所>"
}
```

- **id 命名规则**：`i*`=库存 · `t*`=进出口 · `j21~j25*`=价格信号（对应 2.1~2.5）· `g*`=其他
- **品种码**：CU/AL/PB/ZN/NI/SN/LC/SI
- **顶层必须同步**：`version`（如 2.4→2.5）、`updated`、`change`、`version_changelog`
- 修改后 `python3 -c "import json; json.load(open('data/indicators_v1.json'))"` 验证 JSON 合法性

**② `api_cache.db` 表结构**（不要手工建，由 refresh_cache.py 写入）：

```sql
CREATE TABLE indicator_cache (
  metric  TEXT,      -- 指标 id，如 j23_lme_cash
  code    TEXT,      -- 品种码，如 PB
  data_json TEXT,    -- {"name","unit","freq","points":[{"date","value"},...]}
  PRIMARY KEY (metric, code)
)
```

`data_json.points` 中 `date` 为 `YYYY-MM-DD`，`value` 为数值。**不要手工 INSERT，一律走 refresh_cache.py**（保证 1 秒限频 + 格式一致）。

### (c) 更新与交接回传记录

**① `STATUS.md` 变更记录行格式**（唯一状态真源）：

```markdown
| 2026-08-29 | **[<任务编号>] <一句话结论>**（<背景>）。<做了什么>。<改了哪些文件>。<验证结果>。已推 `<commit短hash>` | <线A/线B> |
```

任务编号规则：`[T7-2.1]`（板块7的子节点2.1）/ `[T8-季节图]`（任务T8的改造项）/ `[DOC]`（纯文档）

**② 回传交接文档**：`docs/handover_<任务编号>_<主题>_<YYYYMMDD>.md`

固定结构（主脑按此验收）：

```markdown
# 回传交接 · <任务编号> · <主题>（YYYY-MM-DD）

#### 一、已完成（逐项可验证）
| 产物 | 文件/路径 | 验证方式 | 结果 |
|---|---|---|---|

#### 二、门禁结果
- check_html.py: X/N PASS
- verify_render.js: X/N PASS
- 线上 curl: <HTTP码 + 字节数>

#### 三、指标入库清单
| id | 名称 | zhiji_id | freq | 数据点数 | 最新日期 |
|---|---|---|---|---|---|

#### 四、未完成/卡点（P0-P3）

#### 五、给主脑的说明
<需要主脑做什么决策、有哪些风险>
```

**闭环标记**：文档顶部加一段 blockquote 标记状态，防止下个 agent 重复劳动：

```markdown
> ✅ **已闭环（YYYY-MM-DD 追加）**：本文档内所有待办已完成。
> - <逐条列已完成项 + commit hash + 验证结果>
> - 下一任务：<指向>
```

---

## 五、循环体系（进度如何保持统一）

```
┌─────────────┐   ①领取任务    ┌─────────────┐
│  主脑(线A)   │ ────────────→ │ 协作agent    │
│ framework-   │               │ (另一台服务器)│
│ tree/        │               │             │
└─────────────┘               └─────────────┘
      │                             │
      │        ②STATUS.md 更新      │
      │  ←────────────────────────  │  ②本地STATUS 或 handover_*.md
      │                             │
      │        ③格式契约产物         │
      │  ←────────────────────────  │  ③回传 handover + indicators 条目
      │                             │
      │        ④验收+合并           │
      │  ←────────────────────────  │
      │                             │
      │        ⑤STATUS 标记闭环      │
      └─────────────────────────→  │
```

**具体机制**：

| 环节 | 谁做 | 用什么 | 保证一致性的手段 |
|---|---|---|---|
| ① 领取 | 主脑 | STATUS.md 待办区加一行 | 唯一真源，任务领取后从待办移到进行中 |
| ② 同步 | 双方 | STATUS.md | 写完 30 秒内 commit+push；**不同时编辑，拿到文件锁才写** |
| ③ 回传 | 协作方 | handover_*.md + indicators 条目 | 严格按第四章格式契约 |
| ④ 验收 | 主脑 | 门禁 + curl + git ls-tree | 三道验证全绿才算完成，不看自述 |
| ⑤ 闭环 | 主脑 | 文档顶部 blockquote | 标 commit hash，防重复劳动 |

**并行安全规则**：
1. **不同两人同时写 STATUS.md** —— 拿文件锁才写，写完立刻释放
2. **不同两人同时改 indicators_v1.json** —— 会冲突。协作方在自己的分支改，回传后由主脑合并
3. **不同两人同时改 chart_kits.py** —— 绝对禁止。这是公共模块，只有主脑改，改完 build 全部页面
4. **api_cache.db 不推 GitHub**（.gitignore 已配 `*.db`）—— 两边各自本地拉数，互不影响
5. **数据冲突时** —— `indicators_v1.json` 的 `version` 字段定序，高版本为准

**主脑验收清单**（收到回传后逐项过）：

```bash
# 1. 代码在远端 main 上
git ls-tree --name-only origin/main | grep pb_XX

# 2. 门禁全绿（在本地跑，不信对方自述）
python3 scripts/check_html.py
node scripts/verify_render.js

# 3. 线上真的可访问且完整
curl -s --max-time 20 -o /tmp/p.html -w "%{http_code} %{size_download}
" <url>
grep -q '</html>' /tmp/p.html && echo "完整" || echo "截断!"

# 4. 图表真实渲染（浏览器打开，读 ECharts 实例）
#    echarts.getInstanceByDom(el).getOption().series 有数据才算真渲染
```

---

## 六、关键坑速查（实测沉淀，勿回退）

| # | 坑 | 解法 |
|---|---|---|
| 1 | chart_kits 的 JS 模板用 `%` 格式化 | 不要用 f-string（f-string 内反斜杠 SyntaxError） |
| 2 | JS 里的 `%` | 要写 `%%` |
| 3 | 标题/备注含 ASCII 双引号 | 炸 Python 字符串 → 统一用中文引号「」 |
| 4 | 观 kline 升序（bars[0]=旧） | 不要反转；但 zhiji series 返回 points **倒序**（最新在前） |
| 5 | check_html 版本检查 | 已改为正则 `indicators_v1\.json v\d+\.\d+`，别写死版本号 |
| 6 | **STATUS.md 追加记录** | patch 的 `
` 会变字面 `
` 不换行！必须用 python 拆行：`raw.split("\n")` 处理后再 join |
| 7 | GitHub Pages 缓存 | `cache-control: max-age=600`，push 后 `sleep 75` 再 curl |
| 8 | **季节图粒度对齐** | 日度→365天类目(`__seasonalizeByDay`)、月度→12月(`__seasonalizeByYear`)，由 `_detect_gran` 自动判断 |
| 9 | **opts 构造时序** | `opts` 在构造时就调用季节函数 → 相关定义必须**内联到图表 JS 内部**，不能依赖 JS_COMMON 注入顺序（`__mdays` 在 JS_COMMON 里后注入会 undefined） |
| 10 | 非空判断 | 用 `==null` 不用 `===null`（`undefined` 会被漏判，`Math.round(undefined)=NaN` 混入数据） |
| 11 | SQLite DB | 不推 GitHub（.gitignore 已配），只推代码和 JSON |
| 12 | 反拷贝 | 前端禁用右键/Ctrl+C/S/P/F12/选中/拖拽（chart_kits 的 ANTI 已内置） |
| 13 | 知几中文分词 | 关键词之间必须**空格分隔**，否则整词匹配误命中 |
| 14 | Pages 验收别只看 200 | 要检查 `</html>` 结尾 + 字节数与本地一致（限流会返回截断响应） |
| 15 | 浏览器缓存 | 改静态文件后加版本号 `?v=20260829` 或强刷 Ctrl+Shift+R |

---

## 七、密钥与环境

**知几 API 三个 key**（写在 `~/.hermes/scripts/zhiji_api.py` 第 19-21 行）：

```python
GUAN_KEY = "guan_a3dbade5e217468006af273fdc772f91"     # 观: 行情+K线
NEWS_KEY = "nws_f5b4b6c653104d0f965fb3463dcf7eed"      # 讯: 新闻快讯
DATA_KEY = "data_8e863643ecc13f11d2c669bdb672f7db"     # 料: 大宗商品指标
```

- 无月度配额，**仅 1 秒/次限频**，批量拉数必须 `sleep 1`
- 调用方式：`python3 ~/.hermes/scripts/zhiji_api.py <子命令> <参数>`
- 子命令：`search <关键词>` / `series <zhiji_id> <start> <end>` / `kline <品种> <周期>`

**本地 API 服务**（可选，用于实时查询而非静态页）：

```bash
python3 /home/ubuntu/framework-tree/scripts/api_server.py 8786
# 浏览器访问 http://127.0.0.1:8786
```

**环境要求**：Python 3.11+、Node 18+、`jsdom`（`npm install jsdom --prefix /tmp`）、`requests`、SSH key 有 `algo23-yunqingtian/framework-tree` 写权限

---

## 八、常用排查命令

```bash
# 服务/端口
ss -tlnp | grep 8786
curl -s -o /dev/null -w "%{http_code}
" http://127.0.0.1:8786/

# GitHub 状态
git log --oneline -10
git ls-tree --name-only origin/main | grep pb_     # 远端有哪些页
git rev-parse HEAD && git rev-parse origin/main    # 本地 vs 远端是否同步
git status --short                                  # 工作区是否干净

# Pages 构建状态
# gh api repos/algo23-yunqingtian/framework-tree/pages → status: "built"

# 数据新鲜度
python3 -c "
import sqlite3, json
c = sqlite3.connect('scripts/api_cache.db').cursor()
r = c.execute('SELECT data_json FROM indicator_cache WHERE metric=? AND code=?', ('j23_lme_cash','PB')).fetchone()
d = json.loads(r[0]); p = d['points']
print(len(p), '点', p[0]['date'], '~', p[-1]['date'])
"

# 指标库版本
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('version', d['version'], '| updated', d['updated'], '| 指标数', len(d['indicators']))"
```

---

## 九、给新 Agent 的第一步

1. 读本文档 → 读 `COLLABORATION.md`（两条线隔离）→ 读 `STATUS.md`（当前进度 + 待办）
2. 确认自己的线（架构/前端 → 线A；指标/数据 → 线B）
3. 跑通一次 Step 4-7（拉数→build→门禁→push），确认环境可用
4. 从 STATUS.md 待办区领一个任务，开工
5. 每完成一个产物就按第四章格式落盘，做完写回传交接文档
6. **禁止**：不读 STATUS.md 直接改代码（可能覆盖别人的工作）

---

## 十、参考资源

| 资源 | 位置 | 用途 |
|---|---|---|
| 已有协作机制 | `COLLABORATION.md` | 两条线隔离 + Git 规范（本文档的前置） |
| 全局状态 | `STATUS.md` | 当前进度、待办、变更记录（唯一真源） |
| 线A 交接 | `docs/handover_a.md` | 架构/前端交接 |
| 线B 交接 | `analysis/iwencai/handover_b.md` | 指标/数据交接 |
| T7 板块1 交接 | `docs/handover_T7_block1_price_20260829.md` | 已完成示例，可参考其闭环标记写法 |
| Prompt 模板 | `prompt_lib/template_v19.md` | 同花顺发散 prompt |
| 词库 | `prompt_lib/dimensions/` `prompt_lib/varieties/` | 维度/品种词库 |
| 批次渲染 | `prompt_lib/render_prompt.py` | 批量渲染 prompt |

---

## 十一、当前项目状态（截至 2026-08-29）

| 项 | 状态 |
|---|---|
| 板块1 价格信号 | ✅ 2.1-2.6 六节点 / 18 图全部上线 |
| 板块2 进出口 | ✅ 6.1-6.4 四节点全部上线 |
| 板块3 库存 | ✅ 4.1 交易所库存子页（完整看板 `pb_stock_v2.html`） |
| 季节图 | ✅ v1.2 按原始粒度对齐（日度365天/月度12月） |
| `indicators_v1.json` | v2.4，共 73 指标 |
| 验证门禁 | check_html 10/10 + verify_render 10/10 ALL PASS |
| 待做 | 供给(3.x)、需求(5.x)、成本利润(7.x)、供需平衡(8.x)；其余 7 品种 |

**已知遗留**：铅库存 8 骨架图仅剩 5 张待补（C03/C04/C06/C10/C14b 等，需同花顺发散或外部数据源）；前 20 会员持仓排名知几无数据（仅 LME/SHFE 总持仓），2.6 页已用观 kline 的量仓结构做替代三图并标注 NOTE。
