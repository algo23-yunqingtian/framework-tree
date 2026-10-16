# DSHD-P67 Wind/Excel 数据打通路径诊断报告

> **报告 ID**: DSHD-P67-WIND-CONNECTION-DIAGNOSIS-001  
> **生成时间**: 2026-10-16 22:00 GMT+8  
> **Agent**: DSHD-P67 工单-D  
> **Branch**: feature/v88-g1  
> **全局 GATE**: CLOSED/HOLD  
> **Release Permit**: NOT_ISSUED  
> **Wind API Calls**: 0  
> **审计边界**: 仅监控、只读、非生产放行  
> **约束**: 本文档仅引用已有证据，不新跑任何 Wind 动作。所有验证清单由 DSHA 执行，DSHD 只做研究不落地执行。  
> **说明**: 本诊断文档不构成生产放行或正式 Release Permit。

---

## 1. 执行摘要

本诊断报告基于 DSHA-P54 在 2026-10-16 16:08–20:35 期间采集的 Wind 连通性测试证据、DSHD-P67 持续监控日志、以及本地文件系统只读检查，对 Wind 桌面客户端 / WindPy API / Excel WDF 插件三条数据获取路径的阻断原因进行假设分析，并给出 DSHA 可执行的验证清单与可行路径对比。

**核心结论**：Wind 数据获取链路当前完全阻断。`windlocal.exe` 立即退出（code=0）、WindPy `w.start()` 返回 ErrorCode=-2、Excel WDF 插件无法加载。三条路径存在共同根因链——**Wind 桌面客户端未成功登录**（`.wind` 用户目录为空，无许可证/会话数据），导致所有下游组件（WindPy、Excel 插件、WSD 公式）均无法工作。

**诊断发现优先级**：

| 优先级 | 发现 | 严重度 | 阻断路径 |
|---|---|---|---|
| P0 | `.wind\WMain\users` 目录为空，无登录数据 | 🔴 阻塞 | 所有路径 |
| P0 | `windlocal.exe` 立即退出（code=0） | 🔴 阻塞 | WindPy + Excel |
| P1 | WindPy `w.start()` ErrorCode=-2 | 🔴 阻塞 | WindPy 直接调用 |
| P1 | Excel WDF 插件加载失败（COM error） | 🟠 高 | Excel WSD 公式 |
| P2 | `wind_config.json` 含明文凭证 | 🟠 高 | 安全隐患（非功能阻断） |
| P2 | SHA256_CHECKSUMS.txt 2 处过期 | 🟡 中 | 完整性校验（非功能阻断） |

---

## 2. 证据源清单

本诊断文档引用的全部证据来自以下已归档文件：

| # | 证据文件 | 行数 | SHA8 | 引用章节 |
|---|---|---|---|---|
| E1 | `tracking_monitor_audit.jsonl` | 53 | `06830FB1` | §3.1-3.3 |
| E2 | `wind_excel_events.jsonl` | 47 | `9B5A209A` | §3.1-3.3 |
| E3 | `DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md` | 601 | `35E930F6` | §3.1-3.3 |
| E4 | `dshd_p67_monitor_log.jsonl` | 504 | — | §4 监控状态 |
| E5 | `wind_config.json` | 38 | — | §3.4 凭证存储 |
| E6 | `.wind` 目录只读检查 | — | — | §3.5 本地配置 |
| E7 | WindPy.dll / WDF.dll 版本检查 | — | — | §3.6 DLL 版本 |
| E8 | `pre_wind_call_guard_check.py` | 1051 | — | §3.7 守卫脚本 |

---

## 3. 症状 → 假设 → 验证项 对照表

### 3.1 症状 A：windlocal.exe 启动立即退出（code=0）

| 项 | 内容 |
|---|---|
| **原始证据** | `tracking_monitor_audit.jsonl` 事件 37 @ 17:19:11 |
| **证据原文** | `"windlocal_exe": "D:\\x64\\windlocal.exe (197392 bytes, x64 PE)"`, `"launch_result": "exits immediately with code 0"`, `"args_tested": 26` |
| **关联证据** | 探索简报 §13.2 发现 1：DSHA 在 17:19:11 尝试启动 Wind 桌面客户端，客户端立即退出（code 0） |

#### 假设 A：本地缺少 Wind 终端许可证/配置（`.wind` 目录空）

| 项 | 内容 |
|---|---|
| **假设描述** | Wind 桌面客户端启动时检测不到有效的用户许可证配置，导致进程立即退出。26 种参数组合均未成功可能是因为缺少登录凭据或许可证文件。 |
| **支持证据** | `.wind\WMain\users` 目录存在但**完全为空**（0 项）。`.wind\WMain\etc` 和 `.wind\WMain\res` 下也无任何配置/许可证文件。这是从未成功登录过 Wind 终端的典型特征。 |
| **反对证据** | 无。文件系统中未发现任何替代的许可证位置。 |
| **验证项** | ✅ 已完成（DSHD 只读检查）：`.wind\WMain\users` 为空；无 `WindUser.ini` 或许可证文件。假设成立。 |

#### 假设 A2：windlocal.exe 启动参数/方式不正确

| 项 | 内容 |
|---|---|
| **假设描述** | DSHA 测试了 26 种参数组合，但可能缺少正确的启动参数（如许可证激活参数、首次运行配置参数）。 |
| **支持证据** | `args_tested: 26` 表明已尝试多种参数组合，均未成功。 |
| **反对证据** | `windlocal.exe` 是 Wind 终端标准入口，即使参数不正确通常也会显示错误消息而非立即退出。 |
| **验证项** | ⏳ 待 DSHA 执行：检查 windlocal.exe 的正确启动参数文档；尝试在命令行运行并观察 stderr 输出。 |

---

### 3.2 症状 B：WindPy w.start() = ErrorCode=-2

| 项 | 内容 |
|---|---|
| **原始证据** | `tracking_monitor_audit.jsonl` 事件 37 + `wind_excel_events.jsonl` 第 33-35 行 |
| **证据原文** | `"windpy_start_error": -2`, `"windpy_error_msg": "Start Error! (desktop client not running)"` |
| **补充证据** | 18:23:50 二次测试：`"All connection attempts failed with ErrorCode=-2. WBox NOT connected."`；`"w.start() and c_start() both return ErrorCode=-2"` |
| **关键发现** | 即使检测到 `WindUpdate.RUN` 进程（PID 21260），`w.start()` 仍返回 ErrorCode=-2。**进程存在 ≠ 终端已登录/已鉴权**。 |

#### 假设 B1：终端只启动未真正登录（进程在 ≠ 已鉴权）

| 项 | 内容 |
|---|---|
| **假设描述** | `WindUpdate.RUN` 进程是 Wind 终端的后台更新组件，不是完整登录会话。ErrorCode=-2 明确指向"桌面客户端未运行"（未建立数据服务连接），即使有相关进程存在。 |
| **支持证据** | ErrorCode=-2 含义为"未连接到 Wind 桌面客户端"。WindPy 文档中 ErrorCode=-2 标准含义为终端未启动或未登录。`.wind\WMain\users` 为空进一步证实无有效登录会话。 |
| **反对证据** | 无。 |
| **验证项** | ✅ 已完成（证据分析）：假设成立。ErrorCode=-2 + 空 users 目录 = 终端从未成功登录。 |

#### 假设 B2：Python 位数（32/64）与 WindPy.dll 不匹配

| 项 | 内容 |
|---|---|
| **假设描述** | 如果 Python 是 64 位而 WindPy.dll 是 32 位（或反之），`import WindPy` 会失败或 `w.start()` 会返回错误码。 |
| **支持证据** | 存在两个版本的 WindPy.dll：`D:\x64\WindPy.dll`（64-bit AMD64, 2.41 MB）和 `D:\bin\WindPy.dll`（32-bit i386, 1.75 MB）。Python 3.12.10 为 64 位。 |
| **反对证据** | `wind_config.json` 中 `windpy_path` 指向 `D:\x64\WindPy.dll`（正确的 64 位版本）。且 `import WindPy` 成功（事件显示 `"WindPy module loaded successfully"`），说明位数匹配。如果位数不匹配，`import` 本身就会失败（`ImportError: DLL load failed`）。 |
| **验证项** | ✅ 已完成（证据分析）：假设不成立。Python 64 位 + WindPy.dll 64 位匹配。`import` 成功是有力反证。 |

#### 假设 B3：WindPy.dll 版本与终端版本不匹配

| 项 | 内容 |
|---|---|
| **假设描述** | WindPy.dll（v1.10.1.00004）与 Wind 终端安装版本（v26.5.1.00003，来自 WDF.dll 版本号）可能存在不兼容。WindPy 版本号和终端版本号使用不同版本体系，可能存在跨版本兼容性问题。 |
| **支持证据** | WindPy.dll ProductVersion=1.10.1.00004，WDF.dll ProductVersion=26.5.1.00003。版本号体系完全不同。ErrorCode=-2 也可能由版本不匹配引起。 |
| **反对证据** | 版本不匹配通常表现为不同的错误码（如模块加载失败），而非 ErrorCode=-2（明确的"终端未运行"）。 |
| **验证项** | ⏳ 待 DSHA 执行：联系 Wind 技术支持确认 WindPy v1.10.1 与终端 v26.5 的兼容性矩阵；检查 WindPy.dll 文件属性中的"产品版本"与终端安装版本是否一致。 |

#### 假设 B4：账号未开通 WindPy 接口权限

| 项 | 内容 |
|---|---|
| **假设描述** | Wind 账号未购买/开通 WindPy API 接口权限，导致 `w.start()` 被服务端拒绝。 |
| **支持证据** | ErrorCode=-2 在某些情况下也可能表示"无权限"。但 WindPy 文档中 ErrorCode=-2 的标准含义是"终端未启动"。 |
| **反对证据** | ErrorCode=-2 的标准含义是"桌面客户端未运行"，而非"权限不足"。权限不足通常返回不同的错误码（如 ErrorCode=-1 或特定权限错误）。 |
| **验证项** | ⏳ 待 DSHC 确认：检查 Wind 账号的 WindPy 接口授权状态；联系 Wind 销售确认该账号是否包含 WindPy API 许可。 |

---

### 3.3 症状 C：Excel WDF 插件已注册但无法加载

| 项 | 内容 |
|---|---|
| **原始证据** | `tracking_monitor_audit.jsonl` 事件 38 |
| **证据原文** | `"wdf_dll": "D:\\x64\\wdf.dll (15MB, registered as COM object)"`, `"clsid": "{6B525F62-654D-4871-9080-19AB64B6EB2C}"`, `"excel_addins_registration": "REGISTERED (LoadBehavior=3)"`, `"comaddins_loading": "FAILED (7 add-ins in list, WDF not found)"`, `"wsd_formula": "FAILED (COM error -2147352567, Invalid formula name)"`, `"simple_formula": "PASS (=1+1 returns 2.0)"` |

#### 假设 C1：Excel 插件依赖已登录的终端常驻，终端没登录 → 插件失效

| 项 | 内容 |
|---|---|
| **假设描述** | WDF Excel 插件是一个 COM 加载项，依赖 Wind 桌面客户端的数据服务连接。终端未登录时，WDF 无法初始化，WSD 公式因此报错。 |
| **支持证据** | 简单公式 `=1+1` 正常执行（返回 2.0），但 WSD 公式报 COM 错误 `-2147352567`（Invalid formula name）。这说明 Excel 本身正常，但 Wind 特定的 WSD 函数不可用。WDF 在 COM 加载项列表中不可见（`7 add-ins in list, WDF not found`），表明 WDF 未成功注册到 Excel 的加载项列表。 |
| **反对证据** | 无。 |
| **验证项** | ✅ 已完成（证据分析）：假设成立。WDF 需要 Wind 终端常驻会话才能加载。终端未登录 → 插件不可用 → WSD 公式报错。 |

#### 假设 C2：WDF 插件注册的 DLL 路径/位数错误

| 项 | 内容 |
|---|---|
| **假设描述** | WDF.dll 注册为 COM 对象时，可能使用了错误的 DLL 路径（如 32 位路径被 64 位 Excel 加载），或注册在错误的 COM 注册表位置。 |
| **支持证据** | `D:\bin\WDF.dll`（32 位）和 `D:\x64\WDF.dll`（64 位）均存在。如果 Excel 是 64 位但 COM 注册指向了 32 位 DLL，加载会失败。 |
| **反对证据** | COM 加载失败的具体错误是"WDF not found"（不在加载项列表中），而非 DLL 加载失败（`LoadLibrary` 错误）。如果是位数不匹配，通常会显示不同的错误。 |
| **验证项** | ⏳ 待 DSHA 执行：检查 `HKCR\CLSID\{6B525F62-654D-4871-9080-19AB64B6EB2C}` 注册表项中 InprocServer32 指向的 DLL 路径；确认该路径的 DLL 与 Excel 位数匹配。 |

---

### 3.4 附加发现：凭证存储问题

| 项 | 内容 |
|---|---|
| **原始证据** | `wind_config.json` 第 6-8 行 |
| **证据原文** | `"username": "[REDACTED-CREDENTIAL]"`, `"password": "[REDACTED-CREDENTIAL]"`（DSHD-P67 仅记录文件存在明文凭证，不复述凭证内容） |
| **风险** | 文件含明文凭证。虽然标记为 `_credentials_usable: false`，但凭证暴露本身构成安全隐患（DEFECT-005）。 |
| **DSHC 已执行** | 账本中凭证已脱敏（`[REDACTED-CREDENTIAL]`）。但 `wind_config.json` 和 git 历史中仍含明文凭证。 |
| **验证项** | ✅ 已完成（DSHD 扫描确认）。处置决策权归 DSHC（轮换凭证 + 清理 git 历史）。 |

---

### 3.5 附加发现：本地配置状态

| 项 | 内容 |
|---|---|
| **`.wind` 目录** | 存在（`C:\Users\YAQH\.wind`），含 `WMain\etc`、`WMain\res`、`WMain\users` 子目录 |
| **`.wind\WMain\users`** | **空**（0 项）——无用户登录数据，无许可证文件 |
| **Wind 安装路径** | `D:\x64\`（165 DLL）和 `D:\bin\`（242 DLL）均存在 |
| **windlocal.exe** | 存在（197,392 bytes, x64 PE） |
| **WindPy.dll** | 存在（x64: 2,411,328B, 64-bit; bin: 1,753,920B, 32-bit） |
| **WindPy 版本** | 1.10.1.00004（两个版本一致） |
| **WDF.dll 版本** | 26.5.1.00003（两个版本一致） |
| **关键结论** | Wind 软件已安装，但从未成功登录。`.wind` 目录结构是安装遗留，不包含任何有效会话数据。 |

---

### 3.6 附加发现：DLL 版本兼容性

| 组件 | 版本 | 位性 | 路径 |
|---|---|---|---|
| Python | 3.12.10 | 64-bit | — |
| WindPy.dll (x64) | 1.10.1.00004 | 64-bit (AMD64) | `D:\x64\` |
| WindPy.dll (bin) | 1.10.1.00004 | 32-bit (i386) | `D:\bin\` |
| WDF.dll (x64) | 26.5.1.00003 | — | `D:\x64\` |
| WDF.dll (bin) | 26.5.1.00003 | — | `D:\bin\` |
| WindExcel 插件 CLSID | — | — | `{6B525F62-654D-4871-9080-19AB64B6EB2C}` |

**分析**：Python 64 位与 WindPy.dll x64 版本匹配。但 WindPy.dll（v1.10.1）与 WDF.dll（v26.5.1）使用完全不同的版本体系，可能存在跨组件兼容性问题。ErrorCode=-2 的标准含义是"终端未运行"，版本不匹配通常不是 ErrorCode=-2 的原因，但应作为次要排查方向。

---

### 3.7 守卫脚本状态

| 项 | 值 |
|---|---|
| **脚本** | `pre_wind_call_guard_check.py` (39,231 B) |
| **检查类别** | 6 类（治理不变量、调用上限、进程状态、HOLD 因子、凭证安全、数据范围） |
| **检查项总数** | 35 |
| **结果** | 31 PASS / 3 FAIL / 1 WARNING |
| **FAIL 原因** | 3 项失败均为存量凭证模式（`wind_config.json` 含明文凭证） |
| **WARNING** | 1 项（非阻断） |
| **凭证硬编码** | 0（凭证从 `wind_config.json` 动态加载） |

---

## 4. 监控状态（截至本报告生成时）

| 项 | 值 |
|---|---|
| **监控轮次** | POLL-221+ @ 21:48:29 |
| **监控版本** | pwsh-7 v3 |
| **轮询间隔** | 60 秒 |
| **治理不变量** | 7/7 全绿（gate=CLOSED/HOLD, release_permit=NOT_ISSUED, wind_api_calls=0, backtest_started=false, continue_after_trip=false, circuit_breaker=READY, hold_block_check=PASS 4/4） |
| **凭证告警** | credential_alert=NONE（自 POLL-146 起） |
| **账本 SHA8** | `06830FB1`（53 行，46,305 B） |
| **Wind 事件 SHA8** | `9B5A209A`（47 行，23,258 B） |

---

## 5. 可行路径对比

| 路径 | 描述 | 前置条件 | 由谁执行 | 风险 | 可行性 |
|---|---|---|---|---|---|
| **路径 1** | 修复 Wind 终端许可+登录 → WindPy 调用 | ① DSHC 提供有效 Wind 凭证（已轮换） ② 确认 Wind 账号包含 WindPy API 许可 ③ 修复或重新安装 Wind 终端使 windlocal.exe 可正常启动 ④ 用户手动登录终端（windlocal.exe）并确认登录成功 | DSHA 执行（在 DSHC 修复凭证/终端后） | 中。需要 DSHC 协调凭证轮换和终端修复。如果账号本身无 WindPy 权限，需要购买许可。 | 🟡 中等——依赖 DSHC 多步骤修复 |
| **路径 2** | 终端登录后 → Excel WSD 公式拉取 | ① 路径 1 的前置条件全部满足 ② Wind 终端成功登录并保持常驻 ③ WDF Excel 插件在终端登录后自动加载 | DSHA 执行 | 低（如果终端登录成功）。WSD 公式方案已被广播授权（G7_CONDITIONAL_RELEASE_BROADCAST-001）。风险仅在于 WDF 插件加载是否随终端登录自动恢复。 | 🟡 中等——依赖路径 1 |
| **路径 3** | 本地离线样本/其它数据源 | ① DSHC 决策批准替代数据源 ② 本地数据覆盖回测所需的时间范围和字段（NI.SHF IC_score 等） | DSHC 决策 + DSHA 执行 | 高。替代数据源可能存在数据质量、时间覆盖、字段完整性差异。需重新评估因子计算管线的数据依赖。 | 🔴 低——需要 DSHC 明确决策 |

---

## 6. 给 DSHA 的验证清单（按优先级排序）

> **重要声明**：以下验证清单由 **DSHA 执行**，DSHD-P67 只做研究不落地执行。每条验证标注了预期结果和可能的后续动作。

### P0 级（必须首先执行）

| # | 验证项 | 命令/操作 | 预期结果 | 如果失败 |
|---|---|---|---|---|
| V01 | 检查 `.wind\WMain\users` 目录状态 | `dir %USERPROFILE%\.wind\WMain\users` | 如果为空，确认无登录数据 | 需要 DSHC 提供有效凭证并手动登录终端 |
| V02 | 在命令行运行 windlocal.exe 并观察 stderr | `D:\x64\windlocal.exe` | 正常情况应显示登录窗口或错误消息，而非立即退出 | 如果立即退出，检查系统日志 `%USERPROFILE%\.wind\logs`（如存在）获取错误原因 |
| V03 | 检查 Wind 终端日志目录 | `dir %USERPROFILE%\.wind\logs` | 日志应包含终端启动尝试的详细错误信息 | 如果无日志目录，说明终端从未完成初始化 |

### P1 级（V01-V03 之后执行）

| # | 验证项 | 命令/操作 | 预期结果 | 如果失败 |
|---|---|---|---|---|
| V04 | 手动启动 Wind 终端并登录 | 双击运行 `D:\x64\windlocal.exe`，输入凭证登录 | 终端正常启动并显示登录成功界面 | 如果无法启动，需要 DSHC 重新安装终端或联系 Wind 技术支持 |
| V05 | 确认终端登录后检查 `.wind\WMain\users` | `dir %USERPROFILE%\.wind\WMain\users` | 应有用户配置/会话文件 | 如果仍为空，说明登录流程失败 |
| V06 | 终端登录状态下测试 WindPy `w.start()` | `python -c "import WindPy as w; print(w.start())"` | 应返回 ErrorCode=0 或连接成功 | 如果仍 ErrorCode=-2，检查 Python 位数匹配和 WindPy.dll 路径 |
| V07 | 检查 WindPy 版本兼容性 | 确认 WindPy.dll 版本（1.10.1）与终端版本（26.5.1）兼容 | Wind 官方兼容矩阵 | 如果不兼容，需要升级/降级 WindPy.dll |

### P2 级（P0/P1 通过后执行）

| # | 验证项 | 命令/操作 | 预期结果 | 如果失败 |
|---|---|---|---|---|
| V08 | 终端登录状态下检查 WDF Excel 插件加载 | Excel → 文件 → 选项 → 加载项 → COM 加载项 | WDF 应出现在加载项列表中 | 如果不在列表中，检查 COM 注册表 `HKCR\CLSID\{6B525F62-654D-4871-9080-19AB64B6EB2C}` 的 InprocServer32 路径 |
| V09 | 终端登录状态下测试 WSD 公式 | 在 Excel 单元格输入 `=[1]!WSD("NI.SHF","IC_score","2024-01-01","2024-01-10")` | 应返回数据值 | 如果 COM 错误，检查 WDF 插件是否正确加载 |
| V10 | 终端登录状态下运行 pre_wind_call_guard_check.py | `python pre_wind_call_guard_check.py --verbose` | 35 检查项全部 PASS | 如果仍 FAIL（凭证模式），确认凭证已轮换 |

### P3 级（可选补充验证）

| # | 验证项 | 命令/操作 | 预期结果 | 如果失败 |
|---|---|---|---|---|
| V11 | 检查 WindPy.dll 注册表注册状态 | `reg query "HKLM\SOFTWARE\WOW6432Node\Wind\WindPy"` | 应存在有效注册 | 如果不存在，运行 Wind 安装程序修复 |
| V12 | 检查 Python 位数匹配 | `python -c "import sys; print(f'{sys.maxsize*2} bit'); import WindPy; print('OK')"` | 应打印 64 位且 import 成功 | 如果 import 失败，检查 `windpy_path` 是否指向正确的 x64 版本 |
| V13 | 检查 Excel 位数与 WDF.dll 位数匹配 | 确认 Excel 位数和 `HKCR\CLSID\{...}\InprocServer32` 指向的 DLL 位数一致 | 位数必须一致 | 如果不一致，重新注册 WDF.dll |

---

## 7. SHA256_CHECKSUMS.txt 过期条目上报

> **DSHD-P67 声明**：以下条目仅做标记上报，DSHD-P67 无权修改 `SHA256_CHECKSUMS.txt`。刷新操作由 **DSHC** 执行。

### 过期条目 ①：Entry #10

| 项 | 当前值 | 实际值 |
|---|---|---|
| **文件** | `data-harbor/dsha_p49_prep/P49_backtest_audit/factor_knowledge_base/P49_pre_gray_check.md` | — |
| **状态** | `❌ MISSING (referenced but not found on disk)` | — |
| **实际磁盘状态** | — | `✅ PRESENT`（13,892 B，创建时间 20:59:35） |
| **原因** | 文件在 SHA256_CHECKSUMS.txt 生成（20:35）之后由 DSHA-P54 创建 | — |

### 过期条目 ②：Entry #20

| 项 | 当前值 | 实际值 |
|---|---|---|
| **文件** | `tracking_monitor_audit.jsonl` | — |
| **SHA256** | `F88FA0696AB8B652EB5E28932714916169D02ECA1D0650125D730A12860EA33D` | — |
| **大小** | 41,923 B | — |
| **实际磁盘状态** | — | SHA256=`06830FB1...`（53 行，46,305 B） |
| **原因** | 账本在 SHA256_CHECKSUMS.txt 生成后追加了 7 条事件（DSHA-P54 V2 离线任务） | — |

### DSHC 操作建议

1. 更新 Entry #10：状态从 `MISSING` 改为 `PRESENT`，大小从 `—` 改为 `13,892`，SHA256 需重新计算
2. 更新 Entry #20：SHA256 从 `F88FA069...` 改为当前实际 SHA256，大小从 `41,923` 改为 `46,305`
3. 建议在 SHA256_CHECKSUMS.txt 末尾新增 DSHA-P54 V2 的 7 个新文件条目（可选，当前不在清单范围内）

---

## 8. 治理约束声明

> **DSHD-P67 声明**：
>
> - 本诊断文档仅用于 Wind/Excel 数据打通路径的研究分析，**不改变全局 GATE**，**不签发 Release Permit**，**不触发生产回测**。
> - 全部治理不变量在审计期间保持 MAINTAINED 状态（POLL-221+ 持续监控中）。
> - **wind_api_calls = 0**，本报告未执行任何 Wind API 调用。
> - **本报告未修改** `tracking_monitor_audit.jsonl`、`wind_excel_events.jsonl`、`SHA256_CHECKSUMS.txt` 或任何 ledger/manifest/checksum 文件。
> - **本报告未包含任何明文凭证**。凭证相关内容以 `[REDACTED-CREDENTIAL]` 占位。
> - DEFECT-003（P49_pre_gray_check.md 缺失）已确认为 RESOLVED（文件存在，13,892 B）。
> - DEFECT-001（P61 扫描器缺失）、DEFECT-002（SHA 漂移执行）、DEFECT-004（Wind 客户端）、DEFECT-005（凭证轮换）仍为 OPEN/BLOCKING 状态，等待 DSHC 回执。
> - 本报告是新增独立文件，提交至 `feature/v88-g1` 分支，不夹带任何明文凭证。
> - 一旦监控发现异常，立即暂停研究任务优先上报。
> - 全局 GATE 维持 CLOSED/HOLD。
> - DSHD-P67 后台监控持续运行中，每 60 秒轮询。
>
> **签名**: DSHD-P67  
> **下次更新**: 收到 DSHC 后续指令 / 发现链路异常 / DSHA-P54 状态推进时
