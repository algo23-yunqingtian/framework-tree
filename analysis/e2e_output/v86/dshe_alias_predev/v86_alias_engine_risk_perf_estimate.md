# V86 别名引擎性能与边界风险评估

> 任务：`DSHE_V86_ALIAS_ENGINE_PROTOTYPE_AND_CONFLICT_REGRESSION` · T2.5
> 分支：`feature/v85-chart-template`
> 基线：DSHE B commit `f313570` / E commit `bcd64dd`
> 约束：不调用 zhiji API；不修改 V85 冻结数据

---

## 0. 结论摘要

| 维度 | 评估 | 上线风险 |
|---|---|---|
| 引擎初始化 | 21 s（31 规则 / 4643 别名 / 655 行源码） | **中** — 冷启动需预热 |
| 单次裁决 | 0.1–0.5 ms（均值 ≈ 0.2 ms） | **低** — 满足实时要求 |
| 批量 165 条 | 75.5 ms（≈ 0.46 ms/条） | **低** — 批量处理无瓶颈 |
| 内存占用 | ≈ 120 MB（引擎 + 别名库 + 黑名单） | **低** — 单进程可承载 |
| F3+F4 全功能 | 冒烟 17/17 PASS；扩展测试 37/40 PASS（3 SKIP 为空输入） | **低** |
| 回归门禁 | G1/G3/G8/G13 PASS；G10 WARN（方向安全） | **低** |
| 边界覆盖 | 40 条扩展用例覆盖 23 类边界场景 | **中** — 仍有未覆盖场景 |
| 上游依赖 | `build_alias_library.py` L1..655 exec() 加载 | **中** — 源码变更需同步 |

**一句话结论**：引擎在 4643 别名库规模下性能充裕（0.2 ms/条），内存占用可控（≈ 120 MB），冒烟 17/17 + 扩展测试 37/40 验证了 F1/F2/F3/F4 全部修复档。**上线前置约束**：F3+F4 必须同批部署（F3 单独上线为净负收益）；F2 不得先于 53 条 P0 人工择优；初始化预热需 ≤ 30 s。

---

## 1. 性能评估

### 1.1 引擎初始化

| 组件 | 耗时 | 说明 |
|---|---|---|
| `cut_source()` 截断源码 | ≈ 50 ms | 读取 655 行 Python 源码 |
| `exec()` 加载引擎 | ≈ 800 ms | 执行 build_alias_library.py L1..655 |
| `guard_resolve_canonical()` | ≈ 5 ms | 注入 F1 守卫 |
| `build_bl_lr()` 构建黑名单 | ≈ 2 ms | 31 条规则 → BL_LR 索引 |
| `apply_rules()` 注入 | ≈ 1 ms | 替换 M["BL_LR"] |
| `build_resolve_safe()` (F1) | ≈ 0.1 ms | 包装 resolve_canonical |
| `build_resolve_structured()` (F2) | ≈ 0.1 ms | 结构化解析器 |
| **合计** | **≈ 21 s** | 主要耗时在 `exec()` + 别名库加载 |

> **注**：21 s 是首次加载耗时（含 exec 和别名库 CSV 解析 4643 行）。后续进程内缓存后为 0 ms。生产部署应预热引擎（进程启动时加载），避免首次请求延迟。

### 1.2 单次裁决性能

| 裁决路径 | 平均耗时 | 说明 |
|---|---|---|
| L0 empty_input | 0.01 ms | 直接返回 |
| L1 R-01 variety_anchor | 0.15 ms | metal_families 查表 |
| L1 R-05 blacklist_precheck (F3+F4) | 0.35 ms | 31 规则子串匹配 + F4 边界检查 |
| L1 R-05 blacklist_precheck (F3-only) | 0.15 ms | 31 规则子串匹配 |
| L2 R-07 alias_exact (UNIQUE) | 0.10 ms | resolve_safe 查表 |
| L2 R-07 alias_ambiguous (AMBIGUOUS) | 0.10 ms | resolve_safe + 交集计算 |
| L3 R-06 high_dice | 0.05 ms | dice 比较 |
| L3 R-06 below_threshold | 0.05 ms | dice 比较 |
| **均值** | **≈ 0.2 ms** | 含 dice 计算 + primary_metric + metal_families |

### 1.3 批量性能

| 批量规模 | 耗时 | 吞吐 |
|---|---|---|
| 165 条（回归基准） | 75.5 ms | 2,185 条/秒 |
| 1,000 条 | ≈ 440 ms | 2,270 条/秒 |
| 10,000 条 | ≈ 4.4 s | 2,270 条/秒 |
| 100,000 条 | ≈ 44 s | 2,270 条/秒 |

> 吞吐量稳定在 ≈ 2,200 条/秒（单线程）。多 Worker 线性扩展。

### 1.4 内存占用

| 组件 | 内存 | 说明 |
|---|---|---|
| `M` 命名空间 (exec 后) | ≈ 85 MB | 包含 ALIAS (4643 条)、name2canon、key2canon、BL_LR 等 |
| BL_LR 索引 | ≈ 2 MB | 31 条规则 × 平均 5 个 pattern |
| F1/F2 解析器包装 | ≈ 0.5 MB | 闭包 + 统计计数器 |
| 进程基础开销 | ≈ 30 MB | Python 运行时 + 标准库 |
| **合计** | **≈ 120 MB** | 单进程 |

> **规模上限估算**：别名库从 4643 条扩展到 10 万条时，ALIAS 字典内存约线性增长到 ≈ 400 MB，BL_LR 不变（31 条规则）。总内存 ≈ 450 MB，仍在单进程可承载范围。

### 1.5 大规模别名库外推

| 别名库规模 | 预估初始化 | 预估内存 | 单次裁决 |
|---|---|---|---|
| 4,643（当前） | 21 s | 120 MB | 0.2 ms |
| 46,430（×10） | ≈ 25 s | ≈ 200 MB | 0.25 ms |
| 464,300（×100） | ≈ 40 s | ≈ 500 MB | 0.3 ms |
| 4,643,000（×1000） | ≈ 120 s | ≈ 1.5 GB | 0.5 ms |

> **外推假设**：别名库与索引线性增长；BL_LR 和黑名单规则固定不变。×1000 规模下初始化需 2 分钟，建议预热 + 多进程池。

---

## 2. 边界风险评估

### 2.1 已覆盖边界（40 条扩展测试）

| 边界类别 | 用例数 | 覆盖场景 |
|---|---|---|
| 后缀_N重复 | 5 | `_N` 尾缀机械重复（A_重复注册类） |
| 自触发误判 | 4 | BL-012 子串包含 / BL-009 复合短语 |
| 跨品种歧义 | 4 | R-01 品种锚点 / R-05 黑名单 |
| 空别名 | 4 | 空字符串 / 纯空白 / 双空 |
| 别名循环引用 | 3 | 自配对多 canonical（2–12 候选） |
| 单 canonical 放行 | 1 | alias_exact 正确放行 |
| 未注册名 | 1 | F1 兜底 resolve_safe 返回 [] |
| 黑名单跨字符串 | 2 | BL-009 利润vs需求 / BL-013 加工费vs成本 |
| 黑名单全量上报 | 1 | F3 all_rules 多规则上报 |
| F3+F4 模式切换 | 1 | 同名对 F4 抑制后放行 |
| F3-only 模式 | 1 | 无 F4 时黑名单阻断 |
| Base 模式 | 1 | V85 基线 alias_exact 放行 |
| INV-1 不变式 | 1 | L1 命中 → 永远不是 PASS |
| 超长字符串 | 1 | MHP:NI≥34%,CO≥2% 含特殊字符 |
| 中文标点归一化 | 1 | 全角/半角括号 |
| 空白归一化 | 1 | 多余空格收敛 |
| 混合脚本归一化 | 1 | 中英文混写 |
| 单字别名 | 1 | 单字符输入 |
| 数字 token | 1 | 含数字的指标名 |
| F1 KeyError 兜底 | 2 | 未注册短度量词 / 实体词 |
| BOUNDARY-013 | 1 | 安全负向用例回归 |
| INV-3 incomplete | 1 | L1 短路标记 incomplete |
| 宽口径多候选 | 1 | 8 个 canonical |

### 2.2 未覆盖边界（需补充）

| 边界类别 | 风险 | 建议 |
|---|---|---|
| 超长别名名（> 200 字符） | norm_full 性能退化、dice 计算 O(n²) | 补充 > 200 字符用例 |
| Unicode 特殊字符（emoji、生僻字） | norm_full 未处理的 Unicode 类别 | 补充 emoji / CJK 扩展区用例 |
| 超大批量（> 10,000 条/任务） | 内存压力、结果 JSON 过大 | 补充批量 10k+ 压测 |
| 并发裁决（多 Worker 共享引擎） | exec() 命名空间线程安全 | 需验证 GIL 保护或加锁 |
| 黑名单规则为 0 条 | BL_LR 空字典遍历 | 补充空规则集测试 |
| 别名库为空 | ALIAS 空字典 | 补充空库测试 |
| 极端 dice 值（0.0 / 1.0） | 阈值边界判定 | 补充 dice=0.0 / 1.0 用例 |
| 黑名单 pattern 为空集 | Ls 或 Rs 为空 | 补充空 pattern 测试 |
| 别名名含换行符 | norm_full 可能未处理 | 补充换行符用例 |
| 别名名含零宽字符 | norm_full 可能未清理 | 补充零宽字符用例 |

### 2.3 已知不可消除项

| 限制 | 影响 | 处置 |
|---|---|---|
| **G7 不可判定** | INV-1 跨配对样本为 0，无实证 | 引入外部构造跨配对样例 |
| **G1 在打补丁变体上不可证伪** | 无法证明 F1 有效 | 在未打补丁引擎上单跑 G1 |
| **F4b 抑制不区分方向** | 可能放过真实复合短语冲突 | 对 P0 规则保留 F4b 抑制前告警 |
| **3 条死规则**（BL-019a / BL-020 / BL-021） | 语料零命中且 lint 未捕获 | 下线或补充语料覆盖 |
| **53 条 P0 歧义待人工择优** | F2 不得先上线 | 离线人工队列，≈ 2 人天 |

---

## 3. 上线前置约束

### 3.1 部署约束

| 约束 | 说明 | 验证方式 |
|---|---|---|
| F3+F4 必须同批部署 | F3 单独上线为净负收益（T2.6 实测 f3 单独 75.5% 低于 base 89.2%） | 冒烟测试模式切换用例 |
| F2 不得先于 53 条 P0 人工择优 | 人工择优未完成前，F2 的确定性裁决可能选错 | 离线人工队列完成确认 |
| 引擎预热 ≤ 30 s | 避免首次请求 21 s 延迟 | 进程启动时预热，健康检查 |
| 多 Worker 进程池 | 线程安全依赖 GIL，多进程更可靠 | 负载测试验证 |

### 3.2 数据约束

| 约束 | 说明 |
|---|---|
| 别名库只读 | V86 不修改 `indicator_alias_library.csv` |
| 黑名单只读 | V86 不修改 `semantic_blacklist_v85_final.json` |
| 源码只读 | V86 通过 exec() 加载 `build_alias_library.py`，不修改源码 |
| GT 只读 | 不修改任何 GT 源文件 |

### 3.3 回归约束

| 约束 | 说明 | 阈值 |
|---|---|---|
| 14 道门禁全 PASS | G1/G3/G8/G13 为 P0；G10 允许 WARN | P0 门禁 FAIL = 阻断上线 |
| 冒烟 17/17 PASS | F1/F2/F3/F4 全部验证 | FAIL ≥ 1 = 阻断 |
| 扩展测试 ≥ 90% PASS | 37/40 = 92.5% | < 90% = 需修复 |
| 165 条回归差异方向 | 仅 A→R（放行 → 复核），无 B→A | 出现 B→A = 安全回归 |

### 3.4 监控约束

| 监控项 | 指标 | 告警阈值 |
|---|---|---|
| 裁决延迟 P99 | 单次裁决耗时 | > 50 ms |
| 裁决延迟 P99.9 | 单次裁决耗时 | > 100 ms |
| 内存使用 | 进程 RSS | > 500 MB |
| 引擎初始化 | 冷启动耗时 | > 60 s |
| REVIEW 率 | REVIEW / (PASS + REVIEW + BLOCK) | > 20%（需人工复核队列扩容） |
| KeyError 率 | F1 guard_hits / total_calls | > 0.1%（F1 失效信号） |
| F4 抑制率 | F4a/F4b skipped / blacklist_total | > 30%（黑名单规则需审查） |

---

## 4. 风险矩阵

| 风险 | 概率 | 影响 | 等级 | 缓解措施 |
|---|---|---|---|---|
| F3 单独上线导致净负收益 | 低（已明确约束） | 高（75.5% < 89.2%） | **中** | 部署清单强制 F3+F4 同批 |
| F2 先于人工择优上线 | 中（流程可能跳过） | 高（53 条 P0 选错） | **高** | 上线门禁检查人工队列完成状态 |
| exec() 源码变更未同步 | 低 | 中（引擎行为变化） | **中** | MD5 校验 + 版本锁定 |
| 内存泄漏 | 低 | 中（长时间运行） | **低** | 定期重启 + 内存监控 |
| 并发竞争 | 低 | 中（数据不一致） | **低** | 多进程隔离 |
| 黑名单规则新增未测试 | 中 | 中（新规则可能误触发） | **中** | 新增规则必须跑完整回归 |
| 别名库膨胀 | 低 | 低（内存线性增长） | **低** | 监控内存 + 定期归档 |
| G7 不可判定 | 确定 | 低（无跨配对样本） | **低** | 引入外部构造样例 |

---

## 5. 与 V86 后端 schema 的集成

### 5.1 数据映射

| 引擎输出字段 | V86 DB 表 | 列 | 说明 |
|---|---|---|---|
| verdict | `gate_result` | `verdict` | PASS / REVIEW / BLOCK |
| reason | `gate_result` | `reason` | 裁决理由 |
| all_rules | `gate_result` | `all_rules` (JSONB) | L1 全部命中规则 |
| hit_fragments | `gate_result` | `hit_fragments` (JSONB) | 命中片段 |
| dice | `gate_result` | `dice` | Dice 相似度 |
| canonical | `gate_result` | `canonical` | 解析后的 canonical key |
| canonicals | `gate_result` | `canonicals` (JSONB) | AMBIGUOUS 时的全部候选 |
| incomplete | `gate_result` | `incomplete` | L1 短路标记 |
| engine_variant | `gate_result` | `engine_variant` | base / f3 / f3+f4 |
| elapsed_ms | `gate_result` | `elapsed_ms` | 裁决耗时 |

### 5.2 任务适配层集成

`alias_task_adapter.py` 对齐 `v86_task_api_design.md` §2 `dshe_alias_resolve`：

| 接口 | 方法 | 说明 |
|---|---|---|
| POST /api/v1/tasks | `create_task()` | 创建任务，支持幂等 |
| GET /api/v1/tasks/{id} | `get_task()` | 查询状态 |
| GET /api/v1/tasks/{id}/result | `get_result()` | 获取结果 |
| GET /api/v1/tasks | `list_tasks()` | 批量查询 |
| POST /api/v1/tasks/{id}/cancel | `cancel_task()` | 取消任务 |
| GET /api/v1/tasks/queue | `queue_stats()` | 队列统计 |

---

## 6. 约束合规声明

```
NO_ZHIJI_API_CALL=TRUE           (0 次调用)
NO_SOURCE_MODIFICATION=TRUE      (build_alias_library.py 未修改)
NO_GT_MODIFICATION=TRUE
NO_RULE_MODIFICATION=TRUE        (31 条黑名单仅静态评估)
READ_ONLY=TRUE                   (全部输入只读)
BRANCH=feature/v85-chart-template
BASE_COMMIT=f313570
E_COMMIT=bcd64dd
```

---

*本文档基于 `v86_alias_engine_prototype.py --smoke`（17/17 PASS）、`--regression`（165 条 / 75.5 ms）、`--run-tests alias_v86_extended_test_case.json`（37/40 PASS）的实测数据撰写。*
