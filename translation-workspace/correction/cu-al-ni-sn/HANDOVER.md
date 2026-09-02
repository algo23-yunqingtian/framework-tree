# 指标纠正协作 · 交接文档（v3）

> 负责人: Windows agent | 时间: 2026-09-02 12:00
> 仓库: github.com/algo23-yunqingtian/framework-tree
> 分支: `indicator-correction-win`
> 独属目录: `translation-workspace/correction/cu-al-ni-sn/`

---

## 📌 新对话开场指令
请在对话开头执行 `read D:\DSH_WORK\周报\MEMORY.md`，然后按其中"常驻规则"继续工作。

---

## 一、已完成清单（13 个板块对照表已生成）

### 铜(CU) — 品种1（全部完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号(2.x) v2 | `CU/2_价格信号/CU_价格信号_correct_v2_20260902.md` | ✅ 15指标 A=12 B=3 C=0 命中率80% |
| 供给(3.1-3.6) | `CU/3_供给/CU_供给_correct_20260902.md` | ✅ 35指标 A=25 B=5 C=6 命中率71.4% |
| 库存(4.1-4.5) | `CU/4_库存/CU_库存_correct_20260902.md` | ✅ 23指标 A=14 B=3 C=6 命中率60.9% |

### 铝(AL) — 品种2（三个板块完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 供给 | `AL/AL_供给_correct_20260902.md` | ✅ 31指标 A=31 B=0 C=0 **100%** |
| 库存 | `AL/AL_库存_correct_20260902.md` | ✅ 11指标 A=8 B=0 C=3 72.7% |
| 进出口 | `AL/AL_进出口_correct_20260902.md` | ✅ 28指标 A=28 B=0 C=0 **100%** |

### 镍(NI) — 品种3（全部5板块完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号 | `NI/NI_价格信号_correct_20260902.md` | ✅ 73指标 A=63 B=1 C=3（含噪声行，核心约35-40个） |
| 供给 | `NI/NI_供给_correct_20260902.md` | ✅ 45指标 A=35 B=10 C=0 |
| 库存 | `NI/NI_库存_correct_20260902.md` | ✅ 32指标 A=30 B=0 C=2 |
| 需求 | `NI/NI_需求_correct_20260902.md` | ✅ 3指标 A=3 B=0 C=0 **100%**（5.1/5.2/5.3各1图） |
| 成本利润 | `NI/NI_成本利润_correct_20260902.md` | ✅ 37指标 A=37 B=0 C=0 **100%** |

### 锡(SN) — 品种4（全部完成）

| 板块 | 文件 | 状态 |
|------|------|------|
| 价格信号 | `SN/SN_价格信号_correct_20260902.md` | ✅ 30指标 A=25 B=0 C=5 |
| 供给 | `SN/SN_供给_correct_20260902.md` | ✅ 45指标 A=29 B=0 C=16 |
| 库存 | `SN/SN_库存_correct_20260902.md` | ✅ 20指标 A=14 B=0 C=6 |
| 需求 | `SN/SN_需求_correct_20260902.md` | ✅ 14指标 A=7 B=0 C=7 |
| 进出口 | `SN/SN_进出口_correct_20260902.md` | ✅ 20指标 A=14 B=0 C=6 |
| 成本利润 | `SN/SN_成本利润_correct_20260902.md` | ✅ 12指标 A=4 B=0 C=8 |

---

## 二、当前状态

- ✅ 15个板块对照表全部完成（CU 3 + AL 3 + NI 5 + SN 6）
- ⏳ **AL价格信号/成本利润/需求** 缺同花顺回复，需先发散

---

## 三、核心方法论

### 知几搜索模板
```python
ZHJ = r"C:\Users\YAQH\.hermes\scripts\zhiji_api.py"
res = subprocess.run(["python", ZHJ, "search", query, "all", "5"],
                    capture_output=True, text=True, timeout=60)
results = json.loads(res.stdout)  # {"results": [...]}
# 分级: A=var_hit&&kw_hit, B=var_hit only, C=no result
```

### 表格解析差异
- **AL/大部分品种**：`| 子节点 | 图名称 | 指标名 | SMM | Mysteel | ... |` → chart=cells[1], names=cells[2:]
- **NI**：Tab分隔，两种格式混用，需从"图名称\t指标名"表头行开始解析
- **SN**：从 `iwencai_r1.md` 正则解析 `- 子节点|图名称\n  旧ID: xxx | 旧名: xxx`

### 已知假命中ID
| 旧ID | 假命中场景 |
|------|---------|
| `ID01659225` 矿产粗铜产量 | 反复被误用（价格/库存/持仓） |
| `ID01552124` USGS精铜库存 | LME库存被误用 |
| `ID01552110` USGS数据 | 铝板块反复误命中 |
| `ID00188823` 电解铜汇总价格 | 仓单被误用为价格 |
| `ID01535718` BHP Spence销量 | 仓单注册/注销被误用 |

---

## 四、Git 状态

最新 commit:
- `c69ba97` 铜库存端23指标对照表
- `df5bf79` 同花顺纠正第一轮
- `e1fd99d` 铜供给端知几验证

**新对话第一步**：
```bash
cd D:\DSH_WORK\周报
git -C D:\DSH_WORK\周报\framework-tree add -A translation-workspace/correction/cu-al-ni-sn/
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git -C D:\DSH_WORK\周报\framework-tree push origin indicator-correction-win
```

---

## 五、下一步优先级

1. **提交当前git改动**（15个对照表已全部生成但未push）
2. **AL价格信号/成本利润/需求**：需同花顺发散后验证
3. **铜价格信号v2**：当前在 `CU/2_价格信号/` 子目录，决定放主目录或保留

---

## 六、环境

| 项 | 状态 |
|---|------|
| git | ✅ `C:\Users\YAQH\AppData\Local\git\cmd` |
| SSH key | ✅ `~/.ssh/id_ed25519_agent` |
| 知几 API | ✅ `~/.hermes/scripts/zhiji_api.py` |
| Python | ✅ 3.12.10 |
| Chrome | ✅ `--remote-debugging-port=9222` |
| 同花顺 | ✅ 已登录 |
| 分支 | ✅ `indicator-correction-win` |

### 脚本清单（`D:\DSH_WORK\周报\` 下）
| 脚本 | 用途 |
|------|------|
| `al_verify.py` | 铝三板块验证（已执行） |
| `ni_verify.py` | 镍验证（v3解析器） |
| `sn_verify.py` | 锡验证（从iwencai_r1.md解析） |
| `cu_price_signal_fix.py` | 铜价格信号v2修正（已执行） |
| `cu_inventory_verify.py` | 铜库存验证（已执行） |
