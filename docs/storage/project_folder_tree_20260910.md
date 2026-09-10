# HAM 回测项目目录结构说明
生成时间：2026-09-10  · 路径：/home/ubuntu/lithium-engine  · 仓库：github.com/algo23-yunqingtian/lithium-engine

## 1. 仓库全貌

```
lithium-engine/                 14M  (git 5.3M + 非git 8.7M)
├── AGENTS.md                   # Agent 入职指南（必读）
├── README.md                   # 系统全貌、7 主体、快速开始
├── sql/                        # 20K — 纯 DDL（DB 不入库）
├── engine/                     # 132K — 博弈引擎核心代码（7 主体逻辑）
├── model_ham/                  # 7.1M — ★ HAM 回测主目录
├── model_lite/                 # 16K — 轻量模型
├── scripts/                    # 124K — 辅助脚本
├── reports/                    # 184K — 全局报告
├── docs/                       # 444K — 架构/逻辑/交接文档
├── data/                       # 4K — 静态数据
├── lithium_backtest.py         # 回测入口脚本
├── .github/                    # 8K — PR 模板/CI
└── .venv_ham/                  # 100K — 独立 venv（不含包）
```

## 2. model_ham/ 回测主目录详解

```
model_ham/
├── ham_factors_full_800d.csv       # 全量因子集（800 日窗口）
├── ham_state_combined.csv          # 状态机组合数据
├── sample_factor.csv               # 样本因子
├── ml_input_features.csv           # ML 输入特征
├── gmm_params.json                 # GMM 参数（GMM 状态聚类）
├── market_state_label.csv          # 市场状态标签
├── ham_ablation.py                 # 消融实验脚本
├── ham_ablation_report.md          # 消融报告
├── ablation_result.md              # 消融结果
├── cluster_input.csv               # 聚类输入
├── state_cluster_report.md         # 状态聚类报告
├── state_distribution_plot.png     # 状态分布图
├── HANDOVER_gmm_state_cluster.md   # GMM 状态聚类交接文档
├── HANDOVER_gmm_v2_spread.md       # GMM v2 spread 交接
├── raw_data/                       # 原始行情/基本面源（198K）
│   ├── lithium_future.csv          # 碳酸锂期货行情（50K）
│   ├── smm_daily.csv               # 碳酸锂现货/冶炼（103K）
│   ├── spot_price.csv              # 现货价格（21K）
│   ├── fundamental_balance.csv     # 供需平衡表（12K）
│   └── readme.md
├── ham_experiment_archive/         # 1.1M — 归档实验记录
│   ├── exp_records/exp301_309/     # exp301-309 结果 PNG/CSV
│   ├── exp_records/exp401_403/     # exp401-403 结果
│   └── intermediate/               # 中间因子/预测 CSV
├── exp3_audit_optimize/            # exp3 审计优化
├── exp4_lookahead_fix/             # exp4 前视偏差修复（核心）
├── exp404_cluster_analysis/        # exp404 聚类分析
├── exp405_factor_screen/           # exp405 因子筛选
├── exp406_fund_factor/             # exp406 资金因子
├── exp407_robustness_check/        # exp407 鲁棒性
├── exp408_conditional_linear/      # exp408 条件线性
├── exp409_ham_dynamic/             # exp409 HAM 动态
├── exp410_fund_dynamic/            # exp410 资金动态
├── exp411_combined/                # exp411 组合
├── exp412_risk_control/            # exp412 风控
├── exp413_robustness/              # exp413 鲁棒性
├── exp414_attribution/             # exp414 归因
├── exp415_audit_stress/            # exp415 审计压力
├── exp416_tail_risk_protect/       # exp416 尾部风险
├── exp417_ham_model_theory/        # exp417 模型理论
├── exp418_production_prepare/      # exp418 生产准备
├── exp419_signal_trade_breakdown/  # exp419 信号交易分解
├── exp420_execution_assumption_bias/ # exp420 执行假设偏差
├── exp420_check/                   # exp420 核查
├── exp423_real_time_validation/    # exp423 实时验证
├── exp424_t1_robustness/           # exp424 T1 鲁棒性（最新）
├── backtest_result/                # 回测结果输出
├── backtest_ic/                    # 回测 IC（信息系数）
├── data/                           # 实验数据
└── reports/                        # 实验报告
```

### 共 23 个 exp 实验目录，exp404 → exp424 连续编号。

## 3. 每个 exp 目录的标准结构

```
expXXX_<name>/
├── data/         # 该实验的输入因子/信号 CSV
├── reports/      # 报告 PNG + MD
├── *.csv         # 实验数据
└── *.py          # 实验脚本（可选）
```

## 4. 版本管理规则

| 规则 | 说明 |
|---|---|
| 分支 | main(生产) / develop(日常) / feature-* / fix-* / docs-* |
| 合并 | main 只接受 PR，主脑 approve + 需测试结果 |
| commit 前缀 | `docs:` / `expNNN:` / `feat:` / `fix:` |
| push 前 | `git pull --no-rebase --no-edit`（避免 non-fast-forward） |
| push 超时 | `GIT_CURL_OPT="--max-time 180 --retry 3" git push` |
| DB 不入库 | `*.db` 已 .gitignore，仓库只携带 sql/schema.sql |
| token 安全 | 绝不写进 shell 命令，用 Python 读 .env |
| 自动推送 | 用 subprocess.run + 检查返回码，绝不 Popen+DEVNULL |

## 5. 当前未提交状态（⚠️ 需先提交）

```
?? model_ham/HANDOVER_gmm_state_cluster.md
?? model_ham/HANDOVER_gmm_v2_spread.md
?? model_ham/ablation_result.md
?? model_ham/cluster_input.csv
?? model_ham/gmm_params.json
?? model_ham/ham_ablation.py
?? model_ham/ham_ablation_report.md
?? model_ham/ham_state_combined.csv
?? model_ham/market_state_label.csv
?? model_ham/state_cluster_report.md
```

**说明**：10 个文件是 GMM 状态聚类 + 消融实验产出，尚未 git add/commit。
最新 commit：3515f99 (exp424 T1鲁棒性诊断交接文档)。

## 6. 三层文件隔离（数据铁律）

| 层 | 路径 | 内容 | 可入库 |
|---|---|---|---|
| Python 库/config | engine/, model_ham/*.py | 纯计算，禁写产业逻辑 | ✅ |
| 框架文档 | docs/, model_ham/*.md | 产业链/核心矛盾/交易逻辑 | ✅ |
| 临时调研数据 | model_ham/raw_data/, data/ | 行情/基本面 CSV | ⚠️ 小文件可入库，大文件/敏感不放 |

## 7. 交接文档体系

| 文档 | 用途 |
|---|---|
| AGENTS.md | 新人入职 + 协作安全 |
| docs/AGENT_LOGIC.md | 7 主体逻辑 + 阈值 |
| docs/ARCHITECTURE.md | 架构数据流 |
| docs/HANDOVER_ARCHIVE.md | 763 行 16 章完整归档 |
| model_ham/HANDOVER_*.md | 各实验交接 |

> 最新实验：exp424 T1 鲁棒性诊断。GMM 状态聚类 + 消融实验产出待提交。
