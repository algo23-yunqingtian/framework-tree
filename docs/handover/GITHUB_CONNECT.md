# GitHub 连接 + 环境搭建卡（实测版 · 2026-08-31）

> 场景：你在**另一台服务器**，没连过这个仓库。
> 目标：clone → 配推送 → 跑门禁 → 开工。
> 本文所有通道结论都经过主脑实测，不是推测。

---

## 0. 实测结论（先看这个，别浪费时间试错）

| 通道 | 实测结果 | 结论 |
|---|---|---|
| SSH `clone` | ✅ 成功（depth 1 约 1-2 分钟） | **首选** |
| SSH 握手 | ✅ `Hi algo23-yunqingtian! You've successfully authenticated` | 通道正常 |
| HTTPS `clone` | ❌ 超时（测 2 次都卡死在 `POST git-upload-pack`） | **别用**，至少别作为首选 |
| 仓库可见性 | `public` | clone 无需权限 |
| 仓库体积 | 5.5MB（远端）→ 43MB（本地） | 很小，慢的是网络不是体积 |

**关键判断**：HTTPS 卡死在 `POST git-upload-pack (175 bytes)` = 协议握手成功、权限没问题，是**传输环节网络限制**。SSH 通道能通。所以**优先走 SSH**。

---

## 1. clone（首选 SSH）

```bash
git clone --depth 1 git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree
```

**前置条件：你的机器上要有已配对的 GitHub SSH key。** 自检：

```bash
ssh -T -o BatchMode=yes -o ConnectTimeout=10 git@github.com
# 成功 → "Hi <你的账号>! You've successfully authenticated..."
# 失败/卡住 → 跳到第 4 节「没有 SSH key 怎么办」
```

> ⚠️ **另一个重要前置**：SSH key 必须绑定到一个**有 push 权限的 GitHub 账号**。
> 如果只用别人的 key clone 下来但那是只读 key，push 会被拒。见第 4 节。

### clone 慢/卡住时

不要干等，加参数重试（`--depth 1` 已经是最大加速手段，只拉最近一层）：

```bash
GIT_SSH_COMMAND="ssh -o ConnectTimeout=15 -o ServerAliveInterval=15" \
  git -c core.compression=9 clone --depth 1 git@github.com:algo23-yunqingtian/framework-tree.git
```

`--depth 1` 足够你的任务用（你不需要历史提交）。**注意**：如果后续任务需要看历史（比如查某文件改动史），再用 `git fetch --unshallow` 补齐。

### clone 后立刻装 hook + 配身份（一次性）

```bash
cd framework-tree
git config core.hooksPath scripts/hooks        # pre-commit：改产物不写 STATUS.md 会被拦
git config user.name  "agent-<你的标识>"
git config user.email "agent-<你的标识>@example.com"
```

---

## 2. 验证基线（防旧基线，必做）

```bash
git fetch origin
git rebase origin/main
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
```

**指标数必须 ≥ 786**。少了说明基线旧或 rebase 失败，**停下报主脑**，别在旧基线上开工（否则 merge 冲突面爆炸）。

最新基线 commit 是 `fcad7eb`（截至本卡发布时）。

---

## 3. 门禁三道（提交前必须全绿）

```bash
python3 scripts/check_html.py       # 静态校验
node scripts/verify_render.js       # 渲染校验（需 node）
python3 scripts/reclaim.py          # 格式契约 + 产物完整性
```

三道全 PASS 才算完成。FAIL 就修完重跑，**不许带病提交**。

**依赖说明**：项目**无 requirements.txt、无 package.json**，脚本全用 Python 标准库（`json/sqlite3/glob/re/urllib`）。不要 `pip install -r`（没有这文件）。

---

## 4. ⚠️ 没有 SSH key / 没有 push 权限怎么办

这是你**唯一可能卡住**的地方。分三种情况：

### 情况 A：有 GitHub 账号，但没有配 key
```bash
ssh-keygen -t ed25519 -C "agent@$(hostname)" -N ""      # 生成，不设密码
cat ~/.ssh/id_ed25519.pub                                 # 复制公钥
```
然后**让用户**去 `https://github.com/settings/keys` → **Add SSH key** → 粘贴公钥 → Add key。
配完再 `ssh -T git@github.com` 验证。**这步需要用户操作，我无法代做。**

### 情况 B：没账号，但用户给你 PAT（ghp_ 开头）
用 HTTPS + token 内嵌（注意：HTTPS 传输可能慢，见坑）：
```bash
export GH_TOKEN="<ghp_开头那串>"
git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/algo23-yunqingtian/framework-tree.git"
```
PAT 由用户在 `https://github.com/settings/tokens` → **Tokens (classic)** → 勾选 **`repo`** → 生成。**只显示一次**，关掉就没了。

### 情况 C：什么都还没有
**只做本地修改 + commit，不要 push**，等用户给凭证。别自己想办法（比如伪造 remote、乱试 token）。

---

## 5. push 的坑（实测过，别踩）

**坑1：`git push --max-time 120` 是静默失败**
`git push` **没有** `--max-time` 参数。传了它只打印 help 并返回 exit 0 —— **看起来成功，实际一个字都没发出去**。这是最隐蔽的失败。

正确写法：
```bash
export GIT_CURL_OPT="--connect-timeout 15 --max-time 300 --retry 5 --retry-delay 10"
git push origin main
```

**坑2：别只看 exit code，二次确认真推上了**
```bash
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git ls-remote origin main | cut -d' ' -f1)
echo "local:  $LOCAL"
echo "remote: $REMOTE"
# 一致 = 推送成功；不一致 = 没推上去
```

**坑3：被拒 non-fast-forward（别人先推了）**
先同步再推，**绝不 `--force`**：
```bash
git pull origin main --no-rebase --no-edit
git push origin main
```

---

## 6. ⚠️ bootstrap_agent.sh 会误报一项（重要）

```bash
bash scripts/bootstrap_agent.sh
```

第 6 项「数据源检查」会跑 `python3 ~/.hermes/scripts/zhiji_api.py search ...`，**这个文件不在 git 仓库里**（含密钥，不进仓库）。所以第 6 项必然 ❌。

**处理**：前 5 项（git 基线 / hook / 指标数 / 门禁 / 死链）必须全绿；第 6 项红灯**可忽略**，回传时注明「zhiji_api.py 不在仓库内，跳过」。

你的任务**完全不碰知几 API**，不需要这个客户端。

---

## 7. 该读哪些文档（只读这 4 个）

`docs/` 下有 15+ 个历史交接文档，多数已过期，别全读。

| 顺序 | 文档 | 作用 |
|---|---|---|
| 1 | `AGENTS.md` | 总入口：红线 + 协作规则 |
| 2 | `STATUS.md` | **唯一真源**：当前进度 + 谁负责什么 |
| 3 | **你的任务卡**（提示词里给） | 具体做什么 |
| 4 | `docs/handover/GITHUB_CONNECT.md` | 本文档 |

`docs/handover/` 内其他文件**按需**看：`INDEX_PAGEMAP_TASKCARD.md`（主看板跳转）/ `CU_GAP_TASKCARD.md`（铜缺口）/ `5METALS_FETCH_BUILD.md`（五金属）/ `DB_LOAD_MAIN.md`（灌库）/ `DB_LOAD_TASKCARD.md` / `DB_LOAD_SPEC.md`。

**别读** `docs/handover_T*.md`、`docs/handover_*.md`（8月27-29 历史交接，已过期）。

---

## 8. 红线（违反过一次，丢过 590 条数据）

1. ❌ **不碰 `data/indicators_v1.json`** —— 主脑独占，改了会覆盖五金属 590 条注册
2. ❌ **不碰 `scripts/chart_kits.py` / `scripts/reclaim.py`** —— 公共模块，主脑独占
3. ❌ **不碰 `scripts/api_cache.db`**，不 `git add -f` 提交任何 `*.db`
4. ❌ **不 `git checkout -f` / `git reset --hard`** —— 会清掉别人未提交改动
5. ❌ **不 `git push --force`**
6. ❌ **不用 `git add .`** —— 精确 add 你改的文件
7. ❌ **不改产物不写 STATUS.md** —— hook 会拦
8. ✅ 有问题先问主脑，别自己发明修法

---

## 9. 回传格式

```
环境搭建完成：
- clone 路径：
- clone 方式：SSH / HTTPS+PAT
- push 权限是否就绪：是/否
- bootstrap 6 项：（第6项 zhiji_api.py 缺失属预期，注明即可）
- 门禁：check_html ?/? / verify_render ?/? / reclaim ?/?
- 指标数核验：（必须 ≥ 786）
- hook 是否已装：

任务完成后另附：
- 产出摘要
- commit hash
- 远程 SHA 与本地一致：是/否
```
