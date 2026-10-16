# Wind Excel 万得插件 因子拉取指南 · DSHA-P54 V6

> **工单**: DSHA-P54 V6 — Excel + 万得插件 模拟人工拉取因子
> **日期**: 2026-07-13
> **执行状态**: ❌ 插件不可用，拉取未完成

---

## 1. 环境状态

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Excel 安装 | ✅ v16.0 | `C:\Program Files\Microsoft Office\Office16\` |
| Excel 进程 | ✅ 可启动/关闭 | win32com 连接正常 |
| Win32COM | ✅ 可用 | win32com.client v2026.08, comtypes v1.4.17 |
| Wind 终端 | ✅ 运行中 | wmain.exe (PID 19612), WBox.exe (PID 2496) |
| Wind 终端窗口 | ✅ 可见 | "Wind金融终端..Alice" |
| **WDF.Addin 注册** | ⚠️ 已注册但禁用 | `HKCU\...\Addins\WDF.Addin`, LoadBehavior=3 (禁用) |
| **WDF 加载** | ❌ 未加载 | Excel AddIns 列表仅5个Office内置项，无WDF |
| **WSD/WSS 函数** | ❌ #NAME? | COM错误码 -2146826259 = 函数未注册 |
| WDF COM ProgID | ❌ 未注册 | HKCR 无 WDF/WindExcel 条目 |
| regsvr32 | ❌ 静默失败 | exit=0 但未创建任何 HKCR 条目 |
| WDF.dll 进程加载 | ❌ 未加载 | Excel/wmain/WBox 进程中均无 WDF.dll |
| CustomUI Ribbon | ❌ 不可访问 | Excel COM 无 CustomUIs 属性 |

---

## 2. WDF.Addin 注册详情

```
HKCU:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin
  FriendlyName  = WDF.Addin
  Description   = Wind.NET Finance Terminal Excel AddIn
  LoadBehavior  = 3 (Not available, not loaded)
  WDF_PATH      = D:\x64\WDF.dll

HKCU:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.XLTaskPanel
  FriendlyName  = Wind Data Feed
  Manifest      = D:\x64\wdf.dll
  LoadBehavior  = 2 (Not available, not loaded)
```

### LoadBehavior 含义

| 值 | 含义 |
|----|------|
| 0 | Available, not loaded |
| 1 | Available, loaded |
| 2 | Not available, not loaded |
| 3 | Not available, not loaded (disabled) |

> **HKCU LoadBehavior 已写为1并验证成功，但Excel重启后回归为3。** 可能原因：HKLM 的 LoadBehavior=3 覆盖 HKCU；或 Excel 策略阻止加载。

---

## 3. Excel Add-ins 列表

Excel 加载了5个加载项，**均非Wind相关**：

| # | Name | 类型 |
|---|------|------|
| 1 | SoucePointPlugin64.xll | XLL |
| 2 | ANALYS32.XLL | XLL |
| 3 | ATPVBAEN.XLAM | XLAM |
| 4 | SOLVER.XLAM | XLAM |
| 5 | EUROTOOL.XLAM | XLAM |

**WDF.Addin 不在列表中。**

---

## 4. WSD/WSS 函数测试结果

```python
# 测试结果
ws.Range('A1').Formula = '=WSS("CU.SHF","close")'
ws.Range('A1').Value   -> -2146826259  # #NAME?

ws.Range('A2').Formula = '=WSD("CU.SHF","close","2025-01-01","2025-01-02")'
ws.Range('A2').Value   -> -2146826259  # #NAME?
```

**结论：WSD/WSS 函数未注册，Excel无法识别。**

---

## 5. COM 注册尝试

| 操作 | 结果 |
|------|------|
| `regsvr32 D:\x64\wdf.dll` | exit=0 (但无HKCR条目产生) |
| `regsvr32 /s D:\x64\wdf.dll` | exit=0 (同上) |
| WDF Add-in OnLoad() | 不可达（不在AddIns列表） |
| VBA ActivateWind | 不可达 |
| WindExcel COM Dispatch | 失败: 无效字符 |
| WDF.DataFeed COM Dispatch | 失败: 无效字符 |

---

## 6. 根因分析

与 P54 V3 (WindPy) 路径一致的根因：

```
Wind 终端 API 桥接层未激活
├── .wind\WMain\ 目录结构存在但零文件
├── 无本地 API 监听端口
├── windlocal.exe 立即退出 (非守护进程)
├── InitWAPI.exe 需要管理员权限
├── regsvr32 静默失败 (COM服务器无法注册)
└── Excel 无法加载 WDF.Addin (COM组件不可用)
```

### 依赖链

```
WSD/WSS 函数
  └── WDF.Addin (Excel COM 加载项)
        └── D:\x64\wdf.dll (COM 服务器)
              └── COM 注册 (HKCR\WDF.Addin)
                    └── ❌ 未注册 (regsvr32 静默失败)

WindPy API
  └── WindPy.dll (D:\x64\)
        └── c_start() -> API 桥接
              └── ❌ 桥接层未激活 (InitWAPI.exe 需要管理员)
```

**两条路径的共同瓶颈：Wind 终端 API 桥接层未激活。**

---

## 7. 已尝试的修复措施

| # | 措施 | 结果 |
|---|------|------|
| 1 | 启用 HKCU WDF.Addin LoadBehavior=1 | ❌ 重启后回归3 |
| 2 | regsvr32 D:\x64\wdf.dll | ❌ 静默失败，无HKCR条目 |
| 3 | regsvr32 /s D:\x64\wdf.dll | ❌ 同上 |
| 4 | 检查 HKLM/HKCU 冲突 | ⚠️ HKLM=3 可能覆盖 HKCU |
| 5 | VBA 调用 ActivateWind | ❌ 无此宏 |
| 6 | xlwings 替代方案 | ⚠️ 可用但需插件加载 |
| 7 | 直接测试 WSD/WSS | ❌ #NAME? |

---

## 8. 后续 DSHC 建议

### 必需操作（管理员权限）

1. **运行 InitWAPI.exe**
   ```
   以管理员身份运行: D:\bin\InitWAPI.exe
   ```
   此工具将初始化 Wind API 桥接层。

2. **启用 Wind 终端 Python API**
   - 打开 Wind 终端 → 工具 → 设置 → API 设置 → 启用 Python API

3. **注册 WDF COM 组件**
   ```
   以管理员身份运行: regsvr32 D:\x64\wdf.dll
   ```

4. **启用 WDF Excel 加载项**
   - Excel → 文件 → 选项 → 加载项 → COM 加载项
   - 勾选 "WindExcel/WDF"

### 或：提供完整配置

- 提供已配置的 `.wind` 目录文件
- 或远程桌面操作 Wind 终端激活 API

### 修复完成后验证

```python
# 测试脚本: test_excel_wind.py
import win32com.client as wc
excel = wc.Dispatch('Excel.Application')
wb = excel.Workbooks.Add()
ws = wb.ActiveSheet
ws.Range('A1').Formula = '=WSS("CU.SHF","close")'
val = ws.Range('A1').Value
assert val != -2146826259, "WSD/WSS still not available"
print(f"WSS returned: {val}")
```

---

## 9. 有色金属因子清单（待拉取）

修复后使用以下配置拉取数据：

### 品种代码 (Wind 标准代码)

| 品种 | Wind 代码 | 说明 |
|------|-----------|------|
| 铜 | CU.SHF | 沪铜主力 |
| 锌 | ZN.SHF | 沪锌主力 |
| 铅 | PB.SHF | 沪铅主力 |
| 锂 | LC.SHF | 广期所碳酸锂 |
| 镍 | NI.SHF | 沪镍主力 |
| 锡 | SN.SHF | 沪锡主力 |

### 指标代码 (Wind)

| 指标 | Wind 代码 |
|------|-----------|
| 日收盘价 | close |
| 成交量 | volume |
| 库存 | inventory |
| 开工率 | operating_rate |
| 现货升贴水 | spot_premium |
| 冶炼利润 | smelting_profit |

### WSD 公式模板

```
=WSD("CU.SHF", "close", "2023-07-13", "2026-07-13")
```

### WSS 公式模板

```
=WSS("CU.SHF", "close")
```

---

## 10. 治理红线状态

| 红线 | 状态 |
|------|------|
| wind_api_calls ≤ 108 | ✅ 0 (无 API 调用) |
| F001-F005 HOLD 因子 | ✅ 4/4 blocked |
| gate=CLOSED/HOLD | ✅ 保持 |
| backtest_started | ✅ false |
| 审计日志只追加 | ✅ 本次追加事件 |
| 明文密码入日志 | ✅ 0次 |

---

## 11. 附录：完整测试日志

```
Excel version: 16.0
Add-ins loaded: 5 (all Office built-in, no WDF)
WDF.Addin registry: LoadBehavior=3 (disabled)
WDF.Addin after HKCU write: LoadBehavior=1 (reverted to 3 after Excel restart)
WSD/WSS test: -2146826259 (#NAME?)
regsvr32 D:\x64\wdf.dll: exit=0, no HKCR entries
WDF.dll in processes: NOT loaded (0/3 processes)
Wind terminal: RUNNING (wmain.exe + WBox.exe)
.winding\WMain\: EXISTS but EMPTY (0 files)
```
