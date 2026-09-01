# 指标纠正协作 · 交接文档（v1）

> 负责人: Windows agent | 时间: 2026-09-02 07:10
> 仓库: github.com/algo23-yunqingtian/framework-tree
> 分支: `indicator-correction-win`
> 独属目录: `translation-workspace/correction/cu-al-ni-sn/`

---

## 一、已完成（逐板块）

### 铜(CU)

| 板块 | 方式 | 产物 | 说明 |
|------|------|------|------|
| 价格信号(2.3) | 同花顺+知几 | `CU/CU_价格信号_iwencai_round1.md` | 同花顺识别3错配+2部分正确，已给SMM/Mysteel精确名 |
| 供给(3.1-3.6) | 知几验证 | `CU/3_供给/CU_供给_correct_20260902.md` | 35指标，A=25 B=5 C=6 |
| 库存(4.1-4.5) | 同花顺+知几 | `CU/CU_库存_iwencai_r1.md` | 31指标已发同花顺 |

### 铝(AL)

| 板块 | 方式 | 产物 | 说明 |
|------|------|------|------|
| 供给(3.1-3.3) | 同花顺+知几 | `AL/AL_供给_iwencai_r1.md` | 16指标已发同花顺 |
| 库存(4.1-4.5) | 同花顺+知几 | `AL/AL_库存_iwencai_r1.md` | 29指标已发同花顺 |
| 进出口(6.1-6.4) | 同花顺+知几 | `AL/AL_进出口_iwencai_r1.md` | 14指标已发同花顺 |

### 镍(NI) / 锡(SN)
⏳ 进行中，脚本 `D:\DSH_WORK\周报\iwencai_ni_sn.py` 后台运行中

---

## 二、工作流

每个板块的 4 步工作流：
1. 从 `mapping/{品种}/step2_match_{品种}.json` 读取旧映射（含错误的 zhiji_id）
2. 发 prompt 给同花顺问财（第一轮纠正旧映射里的错 ID + 第二轮追问 SMM/Mysteel 精确全称）
3. 把同花顺给的精确名搜知几验证
4. 汇总写对照表到 `translation-workspace/correction/cu-al-ni-sn/{品种}/{品种}_{板块}_correct_YYYYMMDD.md`

### CDP 连接参数
- WebSocket: `ws://127.0.0.1:9222/devtools/page/78696523E1B3D5DF181576047B52D487`（同花顺问财页面）
- Chrome 必须以 `--remote-debugging-port=9222` 启动
- 每次发送前需：点击"新对话" → 等编辑器清空(len=1) → 定位 ChatInput 组件 → setText → 点 send-button

### 关键坑位（已踩过的）
1. **同花顺编辑器清空**：点击"新对话"后必须检查编辑器 innerText 长度回到 1，否则残留内容会让 sendBtn 状态混乱
2. **ChatInput 组件**：每次新对话后组件可能重建，必须重新 `FIND_CI_JS` 定位
3. **prompt 分片**：每片 ≤500 字，避免 expression 超长截断
4. **同花顺限流**：间隔 <90s 可能触发"暂时处理不过来了"，脚本内置 30s 间隔（已缩短）
5. **生成完成判据**：等"内容由AI生成，不构成投资建议"页脚出现，超时 10 分钟
6. **知几 API 限流**：1秒/次，脚本已内置 1.1s 间隔
7. **知几搜索词**：中文关键词必须空格分隔，否则整词匹配误命中
8. **假命中识别**：hit_name 含"铜"但指向"矿产粗铜：中国"→ 实际是假命中

### 后台脚本
- `D:\DSH_WORK\周报\iwencai_ni_sn.py` — NI+SN 批量跑同花顺（间隔30s）
- `D:\DSH_WORK\周报\iwencai_batch2.log` — 运行日志

---

## 三、Git 状态

```
分支: indicator-correction-win
已 push 的 commit:
  e1fd99d [T-CU-3][B] 铜供给端3.1-3.6共35指标知几验证对照表(A=25 B=5 C=6)
```

待 push 的本地产物（未 commit）：
- CU_价格信号_iwencai_round1.md
- CU_库存_iwencai_r1.md
- AL_供给/库存/进出口_iwencai_r1.md
- NI/SN 各板块（脚本运行中）

---

## 四、下一步

### 立即执行（当前新对话）
1. 继续跑 NI 和 SN 的同花顺 prompt（脚本已后台运行）
2. NI/SN 跑完后，汇总所有品种的对照表
3. 对每个品种做**第二轮**：用同花顺第一轮给的 SMM/Mysteel 精确名逐条搜知几，确认 zhiji_id
4. 写最终对照表到 `translation-workspace/correction/cu-al-ni-sn/{品种}/{品种}_{板块}_correct_{日期}.md`
5. commit + push 到 `indicator-correction-win` 分支

### 并行策略（用户要求）
- **线1**：跑完品种1（铜）所有节点 → 开始线2
- **线2（并行）**：
  - A: 继续跑品种2-4（铝/镍/锡）的每个节点
  - B: 对品种1（铜）每个节点做知几验证 + 最终对照表

### 已知缺口
- SN 没有 audit 文件，从 step2_match_SN.json（141条）处理
- AL 旧映射缺价格信号/成本利润/需求，需补充发散
- NI 旧映射缺进出口，需补充发散

---

## 五、环境检查清单

| 项 | 状态 | 备注 |
|---|---|---|
| git | ✅ | `C:\Users\YAQH\AppData\Local\git\cmd` |
| SSH key | ✅ | `~/.ssh/id_ed25519_agent`，已认证 |
| 知几 API | ✅ | `~/.hermes/scripts/zhiji_api.py` |
| Python | ✅ | 3.12.10 + websocket + requests |
| Chrome | ✅ | `--remote-debugging-port=9222` |
| 同花顺登录 | ✅ | 问财页面已打开 |
| 分支 | ✅ | `indicator-correction-win` 已建已推 |