# T6b 交接文档 — 季节图"历年各一条线"改造（2026-08-28）

> **给新会话读。** 第一步：读本文件 + `framework-tree/STATUS.md` + `git status`。
> GitHub 仓库：`algo23-yunqingtian/framework-tree`（SSH 推送）。当前分支：`main`（未提交改动）。
> 线上版本：v3（已上线，**季节图是 12 月均值线，不是历年线**）。

---

## 一、一句话状态

**✅ 已完成并上线（v1.1）。** 括号 bug 已修复、三道验证全绿、已推 main `767221e`、线上 4 页 curl 验证 `__seasonalizeByYear` 均 ≥1。**本任务已闭环，无需继续操作。**

- ✅ 用户已确认：季节视图改为"最近 5 年各一条线 + 图例标年份"
- ✅ `chart_kits.py` 已改完（新增 `__seasonalizeByYear` 函数 + 重构 `chart_line_t`）
- ✅ `check_html.py` 已改完（验证 token 更新为 `__seasonalizeByYear`）
- ✅ `verify_render.js` 已改完（验证历年 series）
- ❌ **发现关键 bug**：`chart_line_t` 模板里 `itemStyle` 行的括号顺序写错，导致 build 出来的 HTML 里 JS 语法错误，`verify_render.js` 全 FAIL
- ❌ **未修复**：本地改动未 commit，线上未更新

---

## 二、用户核心需求

**季节视图从"1 条 12 月均值线"改为"历年各一条线 + 图例标年份"。**

| 旧版（v3 已上线） | 新版（待上线） |
|---|---|
| 横轴 1-12 月，一条平均线 | 横轴 1-12 月，每年一条线 |
| 无图例 | 图例显示年份（2022年、2023年...） |
| 无法对比历年 | 可对比历年同期差异 |
| 用户反馈："看不出可比性" | 用户反馈："这样才有可比性" |

**默认显示最近 5 年**（2022-2026），由 `seasonal_max_years=5` 控制。

---

## 三、已完成的工作

### 1. `chart_kits.py` 改造（已完成，但有括号 bug）

**新增 `__seasonalizeByYear(arr, years, palette)` 函数**：
- 输入：原始时序数据 + 年份列表 + 调色板
- 输出：历年 series 数组，每 series 一条线，name 含"年"字
- 逻辑：按年份分组，每月 12 个值，过滤非空<3 年的年份，颜色循环使用 palette

**重构 `chart_line_t`**：
- 新增参数 `seasonal_max_years=5, seasonal_min_year=None, seasonal_max_year=None`
- 季节视图 opts.se.series 改为 `window.__seasonalizeByYear(window['__data_X'], __yrs_X, __pal_X)` 动态生成
- legend 动态从 `__yrs_X` 映射年份名

**位置**：`scripts/chart_kits.py` 第 73-132 行（`chart_line_t` 函数）+ 第 244-252 行（`JS_COMMON` 里的 `__seasonalizeByYear` 定义）

### 2. `check_html.py` 更新（已完成）
- `COMMON_JS_TOKENS` 从 `["function __seasonalize", ...]` 改为 `["function __seasonalizeByYear", ...]`
- 第 7 项季节真数据检查从 `window.__seasonalize(__d)` 改为 `window.__seasonalizeByYear + __yrs_ + __pal_`

### 3. `verify_render.js` 更新（已完成）
- 校验点从"12 月均值"改为"历年 series"：
  - `__seasonalizeByYear` 函数存在
  - 从 `opts.se.series` 直接读真实生成的 series
  - 验证：series 数量≥3、每条线 12 月、非空月份≥3、图例名含"年"
  - 切换后验证 setOption 是否收到历年 series

### 4. 4 个 build 脚本（**不需要改**）
公共模块改了，4 个 build 脚本自动继承新逻辑。

---

## 四、⚠️ 关键 bug（必须修）

### 现象

`verify_render.js` 跑出来 3 页 FAIL，报 `SyntaxError: Unexpected token '}'`，错误位置：
```
itemStyle:{color:'#9b6bb5'},label:{show:false}}}]}]
```

### 根因

`chart_line_t` 模板里 `itemStyle` 行的括号顺序写错了。

**当前错误版本**（`scripts/chart_kits.py` L113）：
```python
"        itemStyle:{color:'%s'},label:{show:false}}}]}]\\n"
```
（字符序列：`}`, `}`, `}`, `]`, `}`, `]` = 6 个字符）

**原 v3 正确版本**（`git show T6b_SEASONAL_V3_BEFORE_20260828:scripts/chart_kits.py` L95）：
```python
"        itemStyle:{color:'%s'},label:{show:false}}}]}]\\n"
```
（字符序列：`}`, `}`, `]`, `}`, `}` = 5 个字符）

**差异**：`]` 和 `}` 的顺序搞反了。原 v3 是 `}}]}}`（6 个字符含逗号），当前是 `}}}]}]`（6 个字符含逗号）。

### 修复方法（1 行）

用 `patch` 工具把 L113 的 `}}}]}}` 改回 `}}]}}`：

```bash
cd /home/ubuntu/framework-tree
# 精确的 patch 命令
python3 << 'PY'
with open('scripts/chart_kits.py') as f:
    s = f.read()
old = "label:{show:false}}}]}]\\n"
new = "label:{show:false}}}]}]\\n"
# 注意：实际字符是 }}]}} (5 chars) 不是 }}}]}] (6 chars)
# 原 v3 是: label:{show:false}}}]}]  <- 6 chars (含 }}]}}  5 + ] 1)
# 当前错的是: label:{show:false}}}]}]  <- 7 chars (含 }}}]}]  6 + ] 1)
PY
```

**正确做法**：直接用 `patch` 工具替换 L113 的字符：
- old: `itemStyle:{color:'%s'},label:{show:false}}}]}]`
- new: `itemStyle:{color:'%s'},label:{show:false}}}]}]`

**但更稳妥**：从原 v3 复制过来：
```bash
git show T6b_SEASONAL_V3_BEFORE_20260828:scripts/chart_kits.py | sed -n '95p' > /tmp/v3_line95.txt
cat /tmp/v3_line95.txt
```
然后手动把 L113 替换成这行。

---

## 五、当前 git 状态

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  modified:   pb_61_raw_material_import.html
  modified:   pb_62_import_export.html
  modified:   pb_63_product_export.html
  modified:   pb_64_overseas_shipping.html
  modified:   scripts/chart_kits.py
  modified:   scripts/check_html.py
  modified:   scripts/verify_render.js
```

- 本地 4 个 HTML 是 build 出来的（有括号 bug，JS 语法错）
- 本地 3 个脚本是改造完的（chart_kits 有括号 bug）
- 线上还是 v3 旧版（能正常用，季节图是均值线）

**未 commit**，可以 `git checkout -- .` 完全回退到 v3。

---

## 六、下一步要做的事（按顺序）

### 1. 修括号 bug（关键！）

```bash
cd /home/ubuntu/framework-tree
# 方法 A：patch 工具
# old_string: "itemStyle:{color:'%s'},label:{show:false}}}]}]\\n"
# new_string: "itemStyle:{color:'%s'},label:{show:false}}}]}]\\n"
# 注意：old 和 new 只差一个 ] 和 } 的位置
```

**最稳妥做法**：从原 v3 直接复制 L95 这一行到当前 L113。

### 2. 重新 build 4 页

```bash
cd /home/ubuntu/framework-tree
python3 scripts/build_pb_61.py
python3 scripts/build_pb_62_demo.py
python3 scripts/build_pb_63.py
python3 scripts/build_pb_64.py
```

### 3. 跑本地三道验证

```bash
# 静态校验
python3 scripts/check_html.py

# JS 语法
for f in pb_6*.html; do
  echo "=== $f ==="
  python3 -c "import re; h=open('$f').read(); m=re.search(r'<script>(.*?)</script>',h,re.DOTALL); open('/tmp/check.js','w').write(m.group(1).strip())"
  node --check /tmp/check.js
done

# 渲染验证
node scripts/verify_render.js
```

三道全绿才能 push。

### 4. commit + push

```bash
cd /home/ubuntu/framework-tree
git add -A
git commit -m "[T6b] 季节图改造: 历年各一条线 + 图例标年份 (v1.1)"
git push origin main
```

### 5. 等 GitHub Pages 构建（1-3 分钟），然后 curl 验证

```bash
for p in pb_61_raw_material_import pb_62_import_export pb_63_product_export pb_64_overseas_shipping; do
  echo "=== $p ==="
  curl -s --max-time 90 "https://algo23-yunqingtian.github.io/framework-tree/${p}.html" | grep -c "__seasonalizeByYear"
done
```

4 页都 ≥1 就是上线成功。

### 6. 用户验收

让用户打开 3 个页面（61/62/63），点「☀ 季节」按钮，确认：
- 能出 5 条线（2022-2026）
- 图例显示年份名
- 颜色不同、能区分

---

## 七、备份 + 回退

- **线上旧版备份**：`/home/ubuntu/backups/framework-tree-t6b-online-before-20260828/`（4 个 v3 HTML）
- **git tag**：`T6b_SEASONAL_V3_BEFORE_20260828`（回退点，指向 v3 已上线状态）
- **回退命令**：
  ```bash
  git checkout T6b_SEASONAL_V3_BEFORE_20260828
  git push origin main
  ```

---

## 八、参考

| 内容 | 路径 |
|---|---|
| 项目全局状态 | `framework-tree/STATUS.md` |
| 公共模块（已改造，有括号 bug） | `framework-tree/scripts/chart_kits.py` |
| 静态校验（已更新） | `framework-tree/scripts/check_html.py` |
| 渲染验证（已更新） | `framework-tree/scripts/verify_render.js` |
| build 脚本（不需要改） | `framework-tree/scripts/build_pb_6X*.py` |
| 线上旧版备份 | `/home/ubuntu/backups/framework-tree-t6b-online-before-20260828/` |
| 回退点 | git tag `T6b_SEASONAL_V3_BEFORE_20260828` |
| 上一版交接 | `framework-tree/docs/handover_T6_P1P2_20260828.md` |

---

## 九、坑速查（本轮新增）

| 坑 | 症状 | 解法 |
|---|---|---|
| **itemStyle 括号顺序错** | `SyntaxError: Unexpected token '}'` | 从原 v3 复制 L95 到当前 L113，`]` 和 `}` 顺序不能反 |
| **`%%` 转义** | `JS_COMMON` 里的 `%` 被 page_html 当格式符 | JS 里的 `%` 要写成 `%%`（比如 `pal[yi %% pal.length]`） |
| **`%s` 参数顺序错位** | `TypeError: not enough arguments` 或变量错位 | 用 python 数 `%s` 数量和 args 数量必须一致，并对照模板每个位置 |
| **var 全局作用域覆盖** | 多图的 `__yrs` / `__pal` 互相覆盖 | 每个图用 `__yrs_<cid>` / `__pal_<cid>` 加 cid 后缀 |
| **series 数组未闭合** | `Unexpected token '}'` | 检查 `series:[{... }]` 末尾是否有 `]` 闭合 |

---

**当前时间**：2026-08-28 22:2x
**下一步**：修括号 → 重新 build → 三道验证 → push → curl 验证 → 用户验收
