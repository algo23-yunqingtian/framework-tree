# HAM 回测流水线迁移方案
生成时间：2026-09-10  · 当前：腾讯云 Agent → 目标：本地服务器 Agent

## 1. 背景与目标

| 项 | 说明 |
|---|---|
| 现状 | HAM 回测跑在腾讯云（40G 磁盘，77% 已用） |
| 目标 | 迁移到本地服务器（空间更大、数据接口权限更高） |
| 分工 | 腾讯云保留轻量代码同步，本地承担高频数据 + 大规模实验 |
| HAM 本体大小 | 仅 14M（迁移成本极低） |

## 2. 资产分类与去向

### ✅ 可同步 GitHub（代码/文档/元数据）

| 资产 | 路径 | 说明 |
|---|---|---|
| 回测引擎代码 | engine/ | 7 主体博弈逻辑 |
| HAM 实验脚本 | model_ham/*.py | exp 实验代码 |
| 实验文档 | model_ham/*.md, docs/ | 交接/报告 |
| 实验元数据 | model_ham/gmm_params.json | 参数配置 |
| 因子定义 | sql/schema.sql | DDL（不含数据） |
| 小 CSV | model_ham/raw_data/*.csv (198K) | 可入库（readme 标注来源） |

### ⚠️ 可迁移到本地服务器（原始数据/高频源）

| 资产 | 路径 | 理由 |
|---|---|---|
| 碳酸锂期货行情 | raw_data/lithium_future.csv | 后续需分钟级采集 |
| 碳酸锂现货/冶炼 | raw_data/smm_daily.csv | SMM 数据，本地权限更高 |
| 现货价格 | raw_data/spot_price.csv | |
| 供需平衡表 | raw_data/fundamental_balance.csv | |
| LME 邮件数据 | lme_bloomberg_data.db (68M) | 本地空间更大 |
| 有色日度数据 | 有色日度数据_*.db (15M) | 本地保留最新 |

### ❌ 禁止上传 GitHub（敏感/版权）

| 资产 | 理由 |
|---|---|
| *.db 数据库文件 | 已 .gitignore，生产 DB 敏感 |
| 知几 API key | 公开页禁止暴露 |
| .env 文件 | 含 token/密钥 |
| 大 CSV 导出（>50M） | 不进版本控制，本地直传 |
| Mysteel/SMM 原始下载 | 可能受数据版权限制 |

### ⚠️ 版权/数据限制清单（不可上传任何公有仓）

| 数据 | 来源 | 限制 |
|---|---|---|
| SMM 碳酸锂数据 | 上海有色网 | 订阅制，不可公开分发 |
| Mysteel 数据 | 我的钢铁网 | 订阅制，不可公开分发 |
| LME 邮件数据 | 彭博终端 | 终端版权，不可公开 |
| 知几 API 响应 | 知几平台 | 数据授权，仅限内部使用 |

> 这些只能留在本地服务器私有目录，不上传 GitHub 也不上传 Datahub。

## 3. 迁移方案（三步走）

### Step 1：腾讯云 → GitHub（代码/文档/元数据）

```bash
cd /home/ubuntu/lithium-engine
git add -A
git commit -m "docs: HAM GMM状态聚类+消融实验产出(GMM v2/cluster/ablation)"
GIT_CURL_OPT="--max-time 180 --retry 3" git push origin main
```

- 同步内容：exp424 代码 + GMM 状态聚类 + 消融实验 + 23 个 exp 文档
- 两边共享：腾讯云 + 本地服务器都 clone 同一仓库
- 预计：~14M 入库（raw_data CSV 一并入库，总量仍小）

### Step 2：原始数据 → 本地服务器（直接传输）

```bash
# 方法 A：rsync 直传（推荐）
rsync -avz --progress \
  /home/ubuntu/lithium-engine/model_ham/raw_data/ \
  user@localhost:/data/lithium-engine/model_ham/raw_data/

rsync -avz \
  /home/ubuntu/lme_bloomberg_data.db \
  /home/ubuntu/有色日度数据_20260910_*.db \
  user@localhost:/data/backups/
```

```bash
# 方法 B：打包 tar 传输
tar czf /tmp/ham_data.tar.gz \
  lithium-engine/model_ham/raw_data/ \
  lme_bloomberg_data.db \
  有色日度数据_20260910_*.db
scp /tmp/ham_data.tar.gz user@localhost:/data/
```

- 预计传输：~100M（CSV + 2 个 DB）
- 本地服务器部署路径：/data/lithium-engine/ 或 /home/ubuntu/lithium-engine/

### Step 3：本地服务器初始化

```bash
# 本地 clone 仓库
git clone git@github.com:algo23-yunqingtian/lithium-engine.git

# 放置原始数据
cp /tmp/ham_data/raw_data/*.csv lithium-engine/model_ham/raw_data/

# 安装依赖（Python 3.11 + 必要包）
pip install -r requirements.txt  # 如有

# 验证回测可运行
python lithium_backtest.py  # 应能复现 exp424 结果

# 验证 GMM 聚类
python model_ham/ham_ablation.py
```

## 4. 分工定义

| 职责 | 腾讯云 Agent | 本地服务器 Agent |
|---|---|---|
| 代码仓库 | ✅ 同步 + PR | ✅ 同步 + PR |
| 实验文档 | ✅ 写入 + push | ✅ 写入 + push |
| 高频行情采集 | ❌ | ✅ 分钟级 akshare/akshare |
| SMM/Mysteel 采集 | ❌（配额受限） | ✅ 本地接口权限高 |
| 知几 API 调用 | ✅（配额可用） | ✅（配额可用） |
| 大规模回测实验 | ⚠️ 磁盘受限 | ✅ 空间充裕 |
| LME 邮件导入 | ❌ | ✅ 本地 cron |
| 看板 GitHub Pages | ✅ 部署 | ✅ 部署 |

## 5. Datahub 上传清单

### ✅ 可上传 Datahub

| 资产 | 说明 |
|---|---|
| 实验报告 Markdown | exp4xx 各报告 |
| 因子定义 JSON | gmm_params.json, factor configs |
| 消融实验结果 | ablation_result.md, ham_ablation_report.md |
| 状态聚类报告 | state_cluster_report.md, HANDOVER_gmm_*.md |
| 回测代码 | model_ham/*.py, engine/ |
| 实验元数据 | exp 目录结构、参数版本 |

### ❌ 不上传 Datahub

| 资产 | 理由 |
|---|---|
| *.db 数据库 | 敏感/版权 |
| 原始行情 CSV | 数据授权限制 |
| SMM/Mysteel/LME 原始数据 | 版权/订阅制 |
| API key / .env | 密钥安全 |

## 6. 清理建议（迁移后）

迁移完成后腾讯云可清理：

| 动作 | 释放 |
|---|---|
| 删 db_backups 旧备份（保留最新1份） | ~1.0G |
| 删 analysis/db_backups 灌库快照 | ~290M |
| 清 pip/uv cache | ~470M |
| 删已迁移的 raw_data CSV（本地已存） | ~200K |
| 评估 output/ 是否保留 | ~220M |
| **合计** | **~1.8G** |

## 7. 执行顺序

1. 提交 HAM 未提交文件 → git push ✅
2. 拉取本地服务器仓库 clone
3. rsync/tar 传输原始数据到本地
4. 本地验证回测 + GMM 可运行
5. 验证通过后，腾讯云执行清理
6. 迁移完成后，腾讯云保留轻量代码同步

## 8. 风险与注意事项

| 风险 | 缓解 |
|---|---|
| 传输中断 | rsync 支持断点续传；tar 可校验 md5 |
| 本地 Python 环境不一致 | 建议用同一版本 3.11 + 同 requirements.txt |
| 数据路径差异 | 脚本用相对路径或 .env 配置绝对路径 |
| GitHub 推送限频 | GIT_CURL_OPT 加重试 |
| Datahub 上传误含敏感数据 | 上传前 `find -name "*.db"` 排除 |

> ⚠️ 本方案为规划文档，**未执行任何迁移或删除操作**。等待用户确认。
