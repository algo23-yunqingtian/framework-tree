# 交接文档 · framework-tree 指标翻译线（Agent A 主脑）· 2026-09-01

> 本文件由 Agent A 主脑在上下文接近上限时自动生成。
> 用法：整段复制本文件（含下方代码块）到新会话，即可无缝继续。

---

## 一、任务是什么

把同花顺 divergence 文件里的**概念指标名**翻译成 **SMM/Mysteel/LME 真实指标名**，建立完整映射表，为看板重建提供精准指标 ID。核心原则：图表设计方案保留，只改指标名。

**当前分工（Agent A = 你，主脑）：**
- ZN（锌）30 节点 ✅ / NI（镍）30 节点 ✅ / CU（铜）30 节点 ✅ / AL（铝）30 节点 ✅ = 120 节点
- Agent B（另一台服务器）负责 SN / SI / LI / PB，B 会推送 audit 文件到 GitHub，由你统一跑知几搜索（Step 2）
- 你只负责 ZN/NI/CU/AL 的映射表（Step 1 审计 + Step 2 知几验证 + Step 3 审核 + Step 4 映射表）

## 二、已完成进度（新 agent 接手时已具备）

1. **Step 0 提取去重：已完成并推送**（commit `ae84cf7`，分支 `translation-workflow`）
   - 修复了 `step0_extract.py`：原脚本只兼容 ZN/NI 管道表格（`| 1 | 图名 | 指标 |`），CU/AL 是历史 tab 格式（3列枚举表 + 4/6列图表表），导致提取失败。重写为按**列数**判别两种格式，4 品种全部 30 节点提取成功。
   - 产出：`analysis/iwencai/{ZN,NI,CU,AL}/concept_indicators.json`（ZN 298 / NI 343 / CU 642 / AL 218 独立指标）
   - 注意 CU 里含矿山/国家名碎片（Antamina、Escondida、秘鲁等 18 个），属正常提取，Step 1 审计会处理
2. **Step 1 审计驱动脚本：已写好**（`translation-workspace/scripts/iwencai_audit_driver.py`），但**尚未全量跑通**（见卡点）

## 三、当前卡点（必须解决才能继续）

**现象**：审计 prompt（17KB）注入编辑器后，`.send-button` 点击无效，消息发不出去；但短消息（如"测试"）能正常发送。

**已排除的原因**：
- ✅ Chrome CDP 正常（端口 9222，iwencai 已登录，多个 /chat tab）
- ✅ 注入成功（编辑器显示 17KB 内容，send-button 存在且未 disabled）
- ✅ 点击序列正确（pointerdown→mousedown→pointerup→mouseup→click）
- ❌ **根因判断：Quill 编辑器只同步 innerHTML 不更新内部 delta 模型**，长内容没被框架捕获。短消息因内容简单侥幸成功。

**推荐解法（未验证，接手者先试这个）**：
1. **优先**：找到页面 Quill 实例，用 `quill.setContents()` 或 `quill.clipboard.dangerouslyPasteHTML()` 同步模型，再点发送。查找方式：`document.querySelector('.ql-editor').__quill` 或遍历全局 `Object.keys(window).filter(k=>k.toLowerCase().includes('quill'))`
2. 次选：用 CDP `Input.insertText` 真实输入事件逐步写入（慢但可靠）
3. 兜底：把长 prompt 拆成 2 次对话发送（先发模板 + 术语，再发 divergence 内容），但会破坏"单次审计"语义，不推荐

**验证成功的标志**：发送后 `document.querySelector('[contenteditable]').innerText.length === 1`（编辑器清空）且 body 出现 AI 回复内容。

## 四、Step 1 审计工作流（修复发送后执行）

每品种 6 个板块组，4 品种共 **24 轮**，每轮 10-15 分钟（含同花顺生成等待 + 50s 限流冷却）：

| 板块 | 节点范围 | 节点数 |
|------|---------|--------|
| 价格信号 | 2.1-2.6 | 6 |
| 供给 | 3.1.1-3.2.4 | 9 |
| 库存 | 4.1-4.5 | 5 |
| 需求 | 5.1-5.3 | 3 |
| 进出口 | 6.1-6.4 | 4 |
| 成本利润 | 7.1-7.3 | 3 |

**运行命令**（`iwencai_audit_driver.py` 已支持断点续跑 state，24 轮可分段跑）：
```bash
# 环境
uv venv /tmp/audit_env -q
uv pip install -q --python /tmp/audit_env/bin/python websocket-client

# 取 ws endpoint（页面级，不是 /devtools/browser/）
python3 -c "
import json, urllib.request
d = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
ws = [t['webSocketDebuggerUrl'] for t in d if t.get('type')=='page' and '/chat' in t['url']]
print(ws[0] if ws else 'NO_CHAT_TAB')
"

# 单板块先验证（成功后再全量）
cd /home/ubuntu/framework-tree
/tmp/audit_env/bin/python -u translation-workspace/scripts/iwencai_audit_driver.py --node ZN_价格信号 --ws "ws://..."

# 全量 24 轮（建议 --start/--end 分段 + 每段后台跑）
/tmp/audit_env/bin/python -u translation-workspace/scripts/iwencai_audit_driver.py --all --ws "ws://..."
```

**驱动脚本已修好的 3 个坑（别回退）**：
1. **发送前必须先点「新对话」清场**（`NEWCHAT_JS`），否则旧会话发送失效
2. **生成完成判定用 body 长度增量**（delta>=3000 且连续 2 次稳定），**禁止**用"模型答案生成完成"字样检测——divergence 内容自带该标记会假阳性（已踩过，产出过假文件已删）
3. **提取用「品种术语参考」锚点截取**，避免抓到 prompt 回显；兜底从"你是X基本面"截取

**产物**：`translation-workspace/audit/{品种}/audit_{板块}.md`，头部带抓取时间+覆盖节点数

## 五、后续步骤（Step 1 完成后）

- **Step 2 知几 API 验证**：从 audit 回复提取 SMM/Mysteel 精确名 → 分词 → 搜知几（`~/.hermes/scripts/zhiji_api.py search/series`，1 秒限频内置）。**此步只有你有 API 密钥，Agent B 会 push audit 文件过来，你统一跑**
- **Step 3 人工审核**：A级直接入库 / B级人工判断 / C级进备用库
- **Step 4 生成映射表** → `translation-workspace/mapping/{品种}/final_mapping.csv`
- **完成后更新 `STATUS.md` + commit + push**（前缀 `[A]`/`[B]`/`[DOC]`）

## 六、关键路径速查

| 项 | 路径 |
|---|---|
| 项目根 | `/home/ubuntu/framework-tree`（分支 `translation-workflow`） |
| Step 0 脚本 | `translation-workspace/scripts/step0_extract.py` |
| Step 1 驱动 | `translation-workspace/scripts/iwencai_audit_driver.py` |
| 审计 Prompt 模板 | `translation-workspace/prompts/audit_prompt_template.md` |
| Step 0 产物 | `analysis/iwencai/{品种}/concept_indicators.json` |
| divergence 原始 | `analysis/iwencai/{品种}/divergence_*.md` |
| Step 1 产物 | `translation-workspace/audit/{品种}/audit_*.md` |
| 知几 API | `~/.hermes/scripts/zhiji_api.py`（key 在此，不进仓库） |
| 项目状态真源 | `STATUS.md`（改产物必须先改它再 commit，否则 pre-commit 拦截） |
| 交接文档 | `translation-workspace/HANDOVER_AGENT_A.md`（原档）+ 本文件 |

## 七、环境与坑（务必遵守）

- Chrome CDP：端口 9222，`--remote-allow-origins` 未开 → websocket 连接必须 `suppress_origin=True`（脚本已内置）
- Python：系统是 PEP 668，禁 pip；用 `uv venv /tmp/audit_env` + `uv pip install websocket-client`
- 文件锁：`python3 ~/.hermes/scripts/file_write_lock.py acquire/release /home/ubuntu/framework-tree`
- 开工前：`git fetch origin && git rebase origin/translation-workflow`（若 main 有变）
- 改 `chart_kits.py` / `reclaim.py` 公共模块必须经主脑；不要推 `*.db`/`.env`
- 数据敏感：网页要反拷贝，不暴露 API key

## 八、质量标准

- 每子节点目标 5-6 张图；删除：统计派生（均值/标准差/分位/环比/同比/增速）、临时不可追踪（检修/排产/停产）、不相关凑数
- 指标名必须与平台**实际命名完全一致**（能直接搜到），无统一口径就写"无统一口径"，不硬凑
- 价格信号板块必须给 LME 精确英文变量名（Cash-3M spread / cancellation ratio / warranted vs unwarranted / COT 字段）
- 映射表 A 级目标 >60%

---

## 九、本次会话最后状态快照（2026-09-01 02:30）

- git：`translation-workflow` 分支，HEAD=`ae84cf7`（Step0 已推送，工作区干净）
- Step 0：4 品种 concept_indicators.json 已生成 ✅
- Step 1：驱动脚本已写好 + 修好 3 坑，但**未全量跑**（卡在长 prompt 发送，见第三节）
- audit 目录：`translation-workspace/audit/ZN/` 空（假阳性产物已删）
- 环境：`/tmp/audit_env` 已建好（websocket-client 1.9.2），CDP 9222 正常，iwencai 已登录
- 上下文占用：约 65%（触发本交接）

**接手第 1 步**：解决第三节发送卡点（Quill delta 同步）→ 跑 `--node ZN_价格信号` 单板块验证 → 全量 24 轮 → 汇报。

> 复制上方「运行命令」块 + 本文件已含全部上下文，直接在新会话粘贴即可开跑。
