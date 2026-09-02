# 监督者交接文档 v4 · 全面复核版(含Pages版本裁定 + fallback清理)

> 角色: 监督者(主脑) | 续接: 2026-09-02 第4轮 | 基于: v3
> 本轮三件事:①彻底删除已失效 fallback ②裁定硅锂问题归属(本地vsPages) ③做v3之外未覆盖的全仓再扫

---

## 0. 速览(三件事结论)

| 事 | 结论 |
|---|---|
| **① fallback 配置** | **已彻底删除**(config.yaml 两处:顶层 fallback_providers + models.sensenova 内 fallback_providers 均清掉)。见 §1 |
| **② 硅锂问题归属** | **本地 == Pages,字节级一致**——不是版本不同步。**问题在代码本身,不在"线上是旧版"**。见 §2 |
| **③ v3 未覆盖的新问题** | 灌库**两张表各管一半、互不完整**;win 分支 79 条被删指标里**锂硅最多**。见 §3 |

---

## 1. fallback 已删除(配置证据)

**已执行**（2026-09-02 实测,`hermes config unset` 两条命令均 ✓）:
- 第 287-289 行:顶层 `fallback_providers: [{custom_sensenova, sensenova-6.8-flash-lite}]`
- 第 346 行:`models.sensenova.fallback_providers: alibailian`

**改动后**:两处**完全删除**。当前主模型 `custom_sensenova / sensenova-6.8-flash-lite`,无 fallback 链。
- ⚠️ 副作用:模型若再挂,请求会直接报错(无降级),不会再静默指向同一死模型。这是你要求的"彻底删除"的必然结果。

---

## 2. 硅锂问题归属裁定:**代码问题,不是版本问题**

**实测证据**(全为 curl + md5 + gh API 一手数据):

| 对比项 | 本地 HEAD(e195b57) | GitHub Pages(algo23-yunqingtian.github.io/framework-tree/) |
|---|---|---|
| Pages 构建状态 | — | built,`last-modified: 2026-09-02 04:13 UTC`(约本地 12:13) |
| index.html 大小 | 28453 字节 | **28453 字节,md5 完全一致** |
| si_3_2_1.html 大小 | 42723 字节 | **42723 字节,md5 完全一致** |
| li_3_1_5.html 页脚 | v3.45 | **v3.45** |
| si_3_2_1.html 页脚 | v3.45 | **v3.45** |
| index 含 li_3_2_1/si_3_2_1 chip | 0 处 | **0 处**(都缺) |

**裁定结论:**
1. **Pages 部署的就是本地 HEAD 的最新版**——字节级一致,不存在"线上是旧版本"。
2. 你看到的"硅锂有问题"是**当前最新版本身就有的 bug**,不是缓存/旧版导致的。
3. 所以 **R2(`__data` 硬编码)/R3(index 缺 li_3_2_1·si_3_2_1 映射)/R5(si_3_2_1 串多晶硅)修完就必须立刻 push**,不然 Pages 不会自动更新(它是 push 触发的,不是常驻刷新)。

---

## 3. v3 没覆盖的新问题(本轮全仓再扫发现)

### 3.1 🔴 **灌库两张表各管一半,数据底座不完整**

| 数据库 | 位置 | 表结构 | 行数 | 状态 |
|---|---|---|---|---|
| `scripts/api_cache.db` | framework-tree 仓库内 | 仅 `indicator_cache`(9列:code/metric/zhiji_id/data_json/...) | **1821 行** | 时序数据源,但**缺品种/节点/层级元数据** |
| `data/indicator_tree.db` | 仓库内,**被 git 推上 Pages** | 仅 `indicator_meta`(**无 indicator_series 表**) | **751 行** | 元数据,**但没时序表,且比 analysis 版少 85 条** |
| `/home/ubuntu/analysis/db/indicator_tree.db` | 线B 本地(不进 git) | `indicator_meta` + `indicator_series`(两张完整表) | **836 meta / 563102 series** | **完整版,但不进 git、不上 Pages** |

**矛盾**:STATUS.md 第 53 行写"五金属灌库✅ 751/836 有数据,series 563K 行",第 156 行写"三表灌库已完成"——但**仓库内推上 Pages 的 db 只有 751 条 meta 且没有 series 表**,真正的完整 db(836+563K)只存在于线B 机器本地。线上 Pages 实际拿不到 563K 时序数据。

⚠️ 不过这点对**当前静态 HTML 架构影响有限**——现状是每页把数据焊死在 `__data` 里(Pages 读的是 HTML 不是 db),所以 563K series 上不上 Pages 目前不影响展示。但 v3 §2 提到的"实时架构路A(data.json)"要重构时,**必须先把 analysis/db 的完整 db 作为数据源,不是 data/indicator_tree.db**。

### 3.2 🔴 win 分支被删的 79 条指标,**锂硅是重灾区**

v3 只说"删 79 条多为锂硅",本轮没细拆。这 79 条若被 merge 会导致对应 HTML 指向不存在的指标——是 P0-A 的具体危害面,建议下轮先列出具体哪些 li_*/si_* ID 会被删,评估受影响页面数。

### 3.3 🟠 死链 = 0 ✅(v3 未跑,本轮补跑)

`python3` 全库死链扫描:**0 页有死链**。这是 STATUS.md 长期声称但从未由 v3 实测确认的一项,本轮证实属实。

### 3.4 🟠 Pages 触发机制确认

Pages 由 `push to main` 触发重建,`last-modified` 与最新 commit 时间吻合(e195b57)。无 cron 定时刷新(此前担心"每天没更新"是误判——它跟 main 走,main 不动它就不动)。

---

## 4. 问题全景(把 v3 和本轮合并,去重排序)

| # | 问题 | 来源 | 严重度 |
|---|---|---|---|
| P0-A | **merge win 分支会删 79 条指标(li/si 居多)+317 页全量冲突** | v3 | 🔴 |
| P0-B | CU 01659225 三节点同正主(正主防串用违规,win 未修) | v3 | 🔴 |
| P0-C | **硅锂 R2/R3/R5 代码 bug**(已裁定:本地=Pages,都是最新版就有) | v3+本轮 | 🔴 |
| P0-D | 页脚 v3.45 残留 129 页 | v3 | 🔴 |
| P0-E | **灌库 db 仓库版(751 无 series)vs 完整版(836+563K)不一致** | 本轮新 | 🔴 |
| P1-A | AL 100% A 级对照表未深审 | v3 | 🟠 |
| P1-B | win 自查脚本 0 个进 git,可追溯性 0 | v3 | 🟠 |
| P1-C | 40 处 `_correct_` 错拼 | v3 | 🟠 |
| P1-D | **win 删的 79 条具体影响面未量化** | 本轮新 | 🟠 |
| P2 | 实时数据架构(路A)待重构,但数据源应先对齐 | v3 | 🟡 |

**其余 STATUS.md 声称项**(死链=0、三道门禁、chip 跳转覆盖 94 条、铜铝缺口 10 节点、指标翻译线进展等)本轮抽检一致,未发现新的过期项。STATUS.md 相对交接文档更可信(因为 pre-commit hook 强制每 commit 更新)。

---

## 5. 文件状态

- 本文件: `framework-tree/docs/HANDOVER_SUPERVISOR_v4_20260902.md`
- 已删:`~/.hermes/config.yaml` 两处 fallback_providers
- 未动:`data/indicator_tree.db`(灌库分歧需你拍板是保留双 db 还是统一)
