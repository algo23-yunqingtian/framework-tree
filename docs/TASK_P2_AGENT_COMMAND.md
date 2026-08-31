# P2 任务：5 个缺指标节点补全

## 你的任务

为 framework-tree 看板补全 5 个"0 注册指标"的节点。每个节点走完整流程：同花顺发散 → 知几验证 → 注册 → 拉数 → 建页 → 门禁。

---

## 前置准备

```bash
# 1. 克隆仓库
cd /home/ubuntu
git clone https://github.com/algo23-yunqingtian/framework-tree.git
cd framework-tree
git config core.hooksPath scripts/hooks

# 2. 自检
bash scripts/bootstrap_agent.sh
# 6 项全绿才开工。红色项先修。

# 3. 确认基线
git log --oneline -3
# 最新 commit 应为 b1d6d8a 或之后
```

---

## 5 个目标节点

| # | 节点ID | 品种 | 板块 | 子节点 | q（搜索方向） |
|---|--------|------|------|--------|--------------|
| 1 | zn_7_3 | 锌(ZN) | 成本利润(7) | 能源成本 | 锌冶炼电力/焦炭/煤成本 |
| 2 | sn_3_2_4 | 锡(SN) | 供给(3) | 利润弹性 | 锡矿开采利润/成本曲线 |
| 3 | si_3_1_3 | 硅(SI) | 供给(3) | 国内矿 | 工业硅国内矿山产量/开工 |
| 4 | si_5_3 | 硅(SI) | 需求(5) | 需求先行 | 多晶硅/有机硅/铝合金需求先行指标 |
| 5 | si_7_3 | 硅(SI) | 成本利润(7) | 能源成本 | 工业硅电力成本/硅煤/石油焦 |

---

## 每个节点的完整流程（6步）

### Step 1: 同花顺发散

打开浏览器访问 `https://www.iwencai.com`，用「新对话」入口（绝不用 /search）。

**Prompt模板（逐节点发，不要一次多节点）**：

```
你是{品种}基本面分析师。请为「{子节点名称}」维度设计图表方案。

题材精准枚举器·复合图设计师：
- 维度：{板块} > {子节点名称}
- 搜索方向：{q}
- 正例关键词参考：{从同花顺AI回答中获取}

要求：
1. 每个子节点设计 2-4 张图（时序图/季节图/结构占比图/价差图）
2. 每张图 1-3 个指标，标注数据源（SMM/Mysteel/Wind/百川/海关）
3. 给出每个指标的中英文名称 + 推荐频率（日/周/月）
4. 明确排除不属于本节点的指标
```

**发散规则**：
- 逐节点发，不要一次发多个节点（实测：一次4节点只出7图，逐节点出18图）
- 只出结果，不要逻辑/相关性分析
- 跨板块指标放备用库，不硬塞进当前节点

### Step 2: 知几验证

对同花顺返回的每个指标，用知几API验证：

```bash
# 搜索
python3 ~/.hermes/scripts/zhiji_api.py search "{指标中文名} {品种}"

# 取时序（确认有连续数据）
python3 ~/.hermes/scripts/zhiji_api.py series {知几ID} 2020-01-01 2026-08-29
```

**打分标准**：
- score ≥ 12 = A（直接注册）
- score 6-11 = B（备选，优先选A）
- score < 6 = C（进备用库标"待外部源"）

**ID格式规则**：
- SMM ID: `a` + 8位数字（如 a10193708）
- Mysteel ID: `ID` + 8位数字
- 自定义扩展: `CUS` + 7位前缀

### Step 3: 注册到 indicators_v1.json

```bash
# 读取当前指标表
python3 -c "
import json
d = json.load(open('data/indicators_v1.json'))
print(f'当前指标数: {len(d[\"indicators\"])}')
"
```

**新增指标格式**（追加到 `indicators` dict）：
```json
{
    "{指标中文名}": {
        "zhiji_id": "a10XXXXXX",
        "source": "SMM",
        "variety": "zn",
        "category": "cost",
        "node": "zn_7_3",
        "unit": "元/吨",
        "freq": "weekly",
        "chart": "7_3_energy_cost"
    }
}
```

### Step 4: 拉数入库

```bash
# 增量拉取（1秒限频，自动写 api_cache.db）
python3 scripts/refresh_cache.py
```

### Step 5: 建页

参考已有 build 脚本模式（如 `scripts/build_pb_71.py`）：

```bash
# 复制最近的同类脚本作为模板
cp scripts/build_pb_71.py scripts/build_{variety}_{node_code}.py
# 编辑：替换品种/指标/标题
```

**图表规范**：
- Dark ECharts 风格
- 每节点 2-4 张图
- 正主指标必须贴合 tree_config 的 q 字段定义
- 辅助指标交叉验证，不喧宾夺主
- f-string 禁止写 JS 模板（用 `%` 格式化 + `%%` 转义）

### Step 6: 门禁三道

```bash
# 1) 静态校验
python3 scripts/check_html.py

# 2) 渲染校验
node scripts/verify_render.js

# 3) 格式契约 + 产物完整性
python3 scripts/reclaim.py
```

**三道全 PASS 才算完成。** 任何 FAIL → 修复 → 重跑。

---

## 提交规范

```bash
# 每完成一个节点就提交
git add -A
git commit -m "[T-{variety}_{node}] 补{板块}·{子节点} {N}指标{M}图"

# 更新 STATUS.md 后 push
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

---

## 硬性红线

- ❌ 不推 `*.db` / `*.pyc` / `.env`
- ❌ 不在公开页暴露知几 API key
- ❌ 不改 `scripts/chart_kits.py`（只有主脑能改）
- ❌ 用 f-string 写 JS 模板
- ❌ 跳过门禁直接提交
- ❌ 改产物文件不更新 STATUS.md（pre-commit 会拦截）

---

## 完成标准

5 个节点全部：
1. indicators_v1.json 注册指标 > 0
2. HTML 页面生成且门禁三道全绿
3. STATUS.md 已更新变更记录
4. push 到 main

---

## 已知坑点

1. **知几配额**：search/series 大批量跑可能耗尽。如遇 429/空响应，等 15 分钟重试。
2. **reclaim FAIL=1**：Windows git log 单引号 bug，非你引入，可忽略。
3. **bootstrap_agent.sh 知几检测**：探测词已改为"锌 社会库存"，不会假阳性报配额耗尽。
4. **同花顺发散必须逐节点**：一次多节点会大幅降低产出质量和数量。
5. **正主防串用**：做某节点前，grep 已有 build 脚本确认指标不是其他页面的正主。

---

## 文件路径速查

| 文件 | 路径 |
|------|------|
| 指标注册表 | `data/indicators_v1.json` |
| 目录树配置 | `data/tree_config.json` |
| 灌库工具 | `scripts/refresh_cache.py` |
| 门禁脚本 | `scripts/check_html.py` / `scripts/verify_render.js` / `scripts/reclaim.py` |
| 知几API | `~/.hermes/scripts/zhiji_api.py` |
| 全局状态 | `STATUS.md` |
| 协作协议 | `docs/COLLABORATION_PLAYBOOK.md` |
| AGENTS.md | `AGENTS.md`（入职必读） |
