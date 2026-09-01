# 指标纠正协作 · 交接文档（v2）

> 负责人: Windows agent | 时间: 2026-09-02 07:25
> 仓库: github.com/algo23-yunqingtian/framework-tree
> 分支: `indicator-correction-win`
> 独属目录: `translation-workspace/correction/cu-al-ni-sn/`

---

## 一、全部完成清单（22 个板块产物已提交）

### 铜(CU) — 品种1（全部完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号(2.3) | `CU/CU_价格信号_iwencai_round1.md` | ✅ 同花顺已识别3错配+2部分正确 |
| 供给(3.1-3.6) | `CU/3_供给/CU_供给_correct_20260902.md` | ✅ 35指标知几验证，A=25 B=5 C=6 |
| 库存(4.1-4.5) | `CU/CU_库存_iwencai_r1.md` | ✅ 同花顺已回复 |

### 铝(AL) — 品种2（部分完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 供给(3.1-3.3) | `AL/AL_供给_iwencai_r1.md` | ✅ 同花顺已回复 |
| 库存(4.1-4.5) | `AL/AL_库存_iwencai_r1.md` | ✅ 同花顺已回复 |
| 进出口(6.1-6.4) | `AL/AL_进出口_iwencai_r1.md` | ✅ 同花顺已回复 |
| 价格信号/成本利润/需求 | — | ⚠️ 旧映射无数据，需补充发散 |

### 镍(NI) — 品种3（全部完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号(2.1-2.6) | `NI/NI_价格信号_iwencai_r1.md` | ✅ 93指标 |
| 供给(3.1-3.6) | `NI/NI_供给_iwencai_r1.md` | ✅ 126指标 |
| 库存(4.1-4.5) | `NI/NI_库存_iwencai_r1.md` | ✅ 89指标 |
| 需求(5.1-5.3) | `NI/NI_需求_iwencai_r1.md` | ✅ 19指标 |
| 成本利润(7.1-7.3) | `NI/NI_成本利润_iwencai_r1.md` | ✅ 39指标 |

### 锡(SN) — 品种4（全部完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号(2.1-2.6) | `SN/SN_价格信号_iwencai_r1.md` | ✅ 30指标 |
| 供给(3.1-3.6) | `SN/SN_供给_iwencai_r1.md` | ✅ 45指标 |
| 库存(4.1-4.5) | `SN/SN_库存_iwencai_r1.md` | ✅ 20指标 |
| 需求(5.1-5.3) | `SN/SN_需求_iwencai_r1.md` | ✅ 14指标 |
| 进出口(6.1-6.4) | `SN/SN_进出口_iwencai_r1.md` | ✅ 20指标 |
| 成本利润(7.1-7.3) | `SN/SN_成本利润_iwencai_r1.md` | ✅ 12指标 |

---

## 二、当前状态

- ✅ 同花顺第一轮 prompt 全部发完（22个板块，13个品种-板块组合）
- ⏳ **第二轮（知几验证）尚未开始**：需要用同花顺给出的 SMM/Mysteel 精确名去搜知几确认 zhiji_id
- ⏳ 最终对照表（correct_YYYYMMDD.md）仅铜供给端和铜价格信号完成

---

## 三、并行策略（用户要求）

### 当前阶段：铜（品种1）第一轮完成 → 开始第二轮

**线A（品种2-4 第一轮）**：
- AL: 补充价格信号/成本利润/需求（旧映射无数据，需先做发散或直接搜知几）
- NI: 第一轮全部完成 → 进入第二轮（知几验证）
- SN: 第一轮全部完成 → 进入第二轮（知几验证）

**线B（铜 第二轮）**：
- 用同花顺给的 SMM/Mysteel 精确名，逐条搜知几
- 写最终对照表到 `CU/{品种}_{板块}_correct_{日期}.md`
- 同时做库存端的最终对照表

---

## 四、Git 状态

```
分支: indicator-correction-win
最新 commit:
  df5bf79 [B] 同花顺纠正第一轮: CU价格信号/库存 + AL供给/库存/进出口 + NI+SN全部 共22产物
  e1fd99d [T-CU-3][B] 铜供给端3.1-3.6共35指标知几验证对照表(A=25 B=5 C=6)
```

---

## 五、关键流程（新对话继续使用）

### CDP 参数
- WebSocket: `ws://127.0.0.1:9222/devtools/page/78696523E1B3D5DF181576047B52D487`（同花顺）
- Chrome 启动参数: `--remote-debugging-port=9222`

### 已确认有效的 CDP JS 片段
```python
# 点击新对话
NEWCHAT_JS = "(() => {...见 iwencai_ni_sn.py...})()"
# 定位 ChatInput
FIND_CI_JS = "(() => {...见 iwencai_ni_sn.py...})()"
# 发送 prompt
SETTEXT_JS = "async () => {...见 iwencai_ni_sn.py...}()"
```

### 每步操作
1. `cdp_eval(NEWCHAT_JS)` → 点新对话
2. 等编辑器清空（len<=1）
3. `ev(FIND_CI_JS)` → 定位 ChatInput
4. `cdp_eval("window.__CI.setText(prompt)")` 或分片收集 → setText
5. 点 send-button（CDP 真实鼠标点击）
6. 等"内容由AI生成"页脚（最多10分钟）
7. 抓取 body.innerText → 切到回复段 → 保存

---

## 六、环境

| 项 | 状态 |
|---|---|
| git | ✅ `C:\Users\YAQH\AppData\Local\git\cmd` |
| SSH key | ✅ `~/.ssh/id_ed25519_agent` |
| 知几 API | ✅ `~/.hermes/scripts/zhiji_api.py` |
| Python | ✅ 3.12.10 |
| Chrome | ✅ `--remote-debugging-port=9222` |
| 同花顺 | ✅ 已登录 |
| 分支 | ✅ `indicator-correction-win` 已推 |