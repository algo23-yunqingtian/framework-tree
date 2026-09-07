# 交接文档 · 主图核验机制 + 同花顺方法论

> 日期：2026-09-03
> 仓库：`/home/ubuntu/framework-tree`
  分支：main（HEAD = origin/main，reset 后干净）
  指标库：1290 条（indicators_v1.json）
  页面总数：328（其中 208 个叶子节点有主图）

---

## 一、本轮完成了什么

### 1. 摸清页面架构 + 主图机制
- 页面是 build_5m_batch.py 生成的静态 HTML，数据点硬编码（`window['__data_echart_*']`）
- 主图选择由 `pick_main(data, node)` 函数决定：原逻辑"挑第一个日频指标"
- `MAIN_METRIC` 字典是"改一行换主图"的把手（key = `品种_节点`，value = 指标 mid）
- 已 patch build_5m_batch.py：`MAIN_METRIC` 支持品种前缀 key + `pick_main` 接受品种参数
- 已验证：NI 4.1 主图从 SHFE 收盘价 → LME 镍库存（成功切换）

### 2. 审计现有主图质量（v2 审计器）
- 脚本：`scripts/audit_mainchart_v2.py`
- 审计结果：`/tmp/mainchart_audit.json`
- **只扫了 4 品种（NI+SN+AL+CU=91 节点）**，ZN/LI/SI/PB 未扫
- 91 节点中：6 占位 + 40 错主图 + 14 口径缩水 + 1 解析失败 + 30 OK

### 3. "迪拜分库"踩坑 + 教训
- NI 4.1 主图被改成"LME 镍库存·迪拜分库"——只是 LME 的一个分库，非全球总量
- 根因：自动选型器只看"名字含库存+非价格"，没核实实际序列口径
- 同花顺明确回答：迪拜分库 ❌ 不适合做主图，LME 全球总计 ✅ 首选

### 4. 去同花顺问财现场提问（3 轮，登录态"田允晴"）
- 第 1 轮：通用筛选标准 → 6 条标准 + 4 层校验 + 3 个"不要" + 速查表
- 第 2 轮：分板块分析范式 → 库存/供给/进出口各 P0-P4 五层
- 第 3 轮：铜库存完整演示 → P0-P4 用真实数字走一遍

### 5. 产出文档清单
| 文件 | 内容 |
|---|---|
| `docs/iwencai_methodology_20260903.md` | 同花顺通用筛选标准（6条+4层校验+速查表+三个不要） |
| `docs/iwencai_board_paradigm_20260903.md` | 分板块 P0-P4 范式（库存/供给/进出口） |
| `docs/iwencai_P0P4_copper_demo_20260903.md` | 铜库存 P0-P4 完整分析演示 |
| `docs/MAINCHART_AUDIT_DESIGN_v1.md` | 核验机制设计文档（v1，基于我自己设计的四层漏斗） |

---

## 二、同花顺方法论核心（对核验机制的直接指导）

### 通用 6 条筛选标准
1. 口径宽度：必须是行业总量或全球口径，不接受单矿区/单企业/单分库
2. 数据频率：日度 > 周度 > 月度
3. 可得性：公开可回溯、历史序列连续≥5年
4. 定价相关性：被交易员每日跟踪
5. 非价格性：价格是结果变量，不能当原因变量
6. 全球可比对性：六品种间口径一致

### P0-P4 分层（跨板块通用）
| 层级 | 回答什么 | 通用标准 |
|---|---|---|
| P0 定方向 | 供需松还是紧 | 全球/全国总量口径，官方源 |
| P1 定节奏 | 拐点何时来 | 内部结构占比，领先信号 |
| P2 验真实 | 总量真实吗 | 第三方高频调研 |
| P3 找错配 | 为什么矛盾 | 地理/品牌结构 |
| P4 防失真 | 数据会骗我吗 | 隐性变量 |

**主图只放 P0+P1**，P2-P4 进辅助/注释。

### 三个"不要"
1. 不要用价格代理指标替代节点指标
2. 不要用高频但窄口径数据替代总量口径
3. 不要忽略内外口径映射关系（LME主图+SHFE副图）

---

## 三、下一步待做

### P0（紧急）
1. **修 v2 审计器品种覆盖 bug**：把 ZN/LI/SI/PB 也扫进来，拿到全 208 节点的问题清单
2. **落地 v3 审计器**：用同花顺 P0-P4 替换我自己设计的 scope_score
   - 判据：主图必须是 P0 层指标；P1 当主图=轻度错配；P2/P3/P4 当主图=严重错配
   - 硬规则：含地名分库→降级；verified=False→降级；价格类在非价格板块→标红
3. **接入门禁**：v3 审计器跑完后红项=0 才允许 push

### P1（重要）
4. 按同花顺速查表逐节点核验：六品种×五节点共 30 个"应然主图" vs 当前 208 个页面的"实然主图"
5. 对齐 MAIN_METRIC 映射表：把同花顺推荐的 P0 指标写入 MAIN_METRIC
6. 重跑 build + 门禁三连 + commit

### P2（后续）
7. 长期架构升级：页面启动时读 data.json + layout.json（配置驱动，不重跑 build）
8. 需求/成本利润板块的 P0-P4 范式（本次只问了库存/供给/进出口）

---

## 四、关键文件路径

| 文件 | 路径 | 说明 |
|---|---|---|
| 指标库 | `data/indicators_v1.json` | 1290 条 dict |
| build 脚本 | `scripts/build_5m_batch.py` | 已 patch MAIN_METRIC + pick_main |
| v2 审计器 | `scripts/audit_mainchart_v2.py` | 只扫 4 品种，需升级 |
| 审计结果 | `/tmp/mainchart_audit.json` | 91 节点结果 |
| 同花顺方法论 | `docs/iwencai_methodology_20260903.md` | 通用标准 |
| 分板块范式 | `docs/iwencai_board_paradigm_20260903.md` | 库存/供给/进出口 P0-P4 |
| 铜演示 | `docs/iwencai_P0P4_copper_demo_20260903.md` | P0-P4 完整分析示例 |
| 核验设计 | `docs/MAINCHART_AUDIT_DESIGN_v1.md` | v1 设计（待升级为 v3） |
| correction 文档 | `translation-workspace/correction/` | 同花顺 A 级正主（含噪音） |
| 文件锁 | `~/.hermes/scripts/file_write_lock.py` | session 必须用飞书完整 ID |

---

## 五、注意事项

1. **correction 文档有噪音**：同花顺 AI 回复本身含归属错配，不能盲抄
2. **知几 API 今日 429 配额已尽**（10000 次），明天恢复
3. **同花顺问财 chat 需登录态**：当前 cookie 有效但可能过期，下次需重新登录
4. **MAIN_METRIC 的 key 格式**：`"NI_4.1"`（品种_节点），不是 `"4.1"`
5. **pick_main 已改签名**：`pick_main(data, node, comm=None)`，comm 用于品种前缀 key 查找
6. **v2 审计器只扫了 4 品种**：ZN/LI/SI/PB 的 117 个节点未审计，全库真实问题数未知
