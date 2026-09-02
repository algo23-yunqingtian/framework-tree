# 监督者交接文档 v1 · 8 品种指标纠正总控

> 角色: 监督者（你 / 本 agent）| 生成: 2026-09-02 | 状态: 新对话续接用
> 仓库: github.com/algo23-yunqingtian/framework-tree (main HEAD 当前 = 904b42a)
> 一句话:**主脑侧硅/锂 P0-P3 已闭环上线但验收发现多项返工项;Windows 侧铜/铝/镍/锡 18/24 板块 + 返工 + P1 注册待做;红线条目待清**。

---

## 0. 三方分工总览

| 方 | 负责 | 分支 | 进度 |
|---|---|---|---|
| **主脑(飞书Hermes)** | 铅/锌/硅/锂 | main | 铅锌✅已上线;硅锂✅已上线但**需返工**(见 §4) |
| **Windows agent** | 铜/铝/镍/锡 | indicator-correction-win | 18/24 板块,**缺6板块+4处返工+未注册** |
| **监督者(你)** | 验收/纠错/总控 | — | 本文件 |

**跨机协作纪律**: 文件锁只在本机生效,跨机必须走 git 分支。主脑在 main 直接改;Windows 在 indicator-correction-win 分支改,做完 push 由主脑 review。

---

## 1. 主脑侧 — 硅/锂现状(已上线,需返工)

**已完成**: 硅 39 页 + 锂 41 页 = 80 页;indicators_v1.json 888 条(v3.46);_origin=correction_* 共 79 条;
三道门禁实测全绿 — check_html 223/223、verify_render 224/224、reclaim 12/12。
站点: https://algo23-yunqingtian.github.io/framework-tree/ (index/si_2_1/li_3 均 200)。
主脑自报"12页"是低估,实际 80 页。

**验收发现的返工项**(§4 有给主脑的完整提示词,可直接转发):

| # | 问题 | 根因 |
|---|------|------|
| R1 | 锂 3.1.5「TC加工费」节点挂的是 ID01349545「碳酸锂生产毛利」 | 毛利本属 7.2(库里 _nodes=["2.6"]),挂错到 3.1.5 |
| R2 | 锂 3.1.5「周频变日」:sub 写 weekly/229点,实为周间隔点被 time 轴画成日均线 | HTML 硬编码 229 点(__data 变量),不从 api_cache 拉;缓存 ID01349545 仅 6 点 |
| R3 | 锂 3.2.1 按钮打不开 | index.html PAGE_MAP 缺 li_3_2_1 映射键;锂供给缺 s1/s2/s3/s6/s8/s9 |
| R4 | 锂供给指标稀(3.2.1 仅 1 指标) | 发散/注册不全 |
| R5 | 硅 3.2.1 串入多晶硅产量/硅锰开工率 | 建页未做归属过滤,同花顺跨品类混推照单全收 |
| R6 | 页脚 v3.45 与库 v3.46 不一致 | 版本号未同步 |

**语义交叉验证结论**: 硅/锂/铜/铝跨品种串用经精确词界扫描为 0(铝里出现铜/镍那类串代码问题**不存在**);串品种只在硅 3.2.1 的"指标名称跨品类"(多晶硅/硅锰)这一处。

---

## 2. 主脑侧 — 铅/锌现状(已验收通过)

| 品种 | 页面 | 站点 | 备注 |
|---|---|---|---|
| 铅 PB 37 页 | 价格/供给/库存/需求/成本 | pb_21_price_structure / pb_71_cost_curve / pb_321_refining_output 均 200 ✅ | 用描述性文件名,别用 pb_0/pb_2_1(不存在) |
| 锌 ZN 42 页 | 全板块 | zn_0 / zn_7_1 均 200 ✅ | 铅锌是主导,已完成 |

---

## 3. Windows 侧 — 铜/铝/镍/锡(待推进)

**分工**: CU/AL/NI/SN,任务卡要求 110 节点/24 板块。
**进度**: 对照表 18/24(75%),分支 5 个 commit,最新 09-02 08:45。

**缺失 6 板块**:
- CU: 需求 5.1-5.3 / 进出口 6.1-6.4 / 成本利润 7.1-7.3
- AL: 价格信号 2.1-2.6 / 需求 5.1-5.3 / 成本利润 7.1-7.3
- NI: 进出口 6.1-6.4

**质量返工 4 处**:
- CU 价格信号 18 指标 14 个 B 级是伪命中(全指向占位 ID01659225 矿产粗铜产量,字段错乱)
- NI 价格信号 67 指标膨胀,应收敛 ≤20
- AL 供给/进出口 100% A 级存疑(需抽查 ID 是否真对应电解铝)
- 4 份文件规范不达标(缺独立 prompt 原文)

**还未注册 P1**: Windows 对照表只停在"出表",未像主脑那样把 ID 注册进 indicators_v1.json。

**给 Windows 的完整任务卡**(对齐主脑标准、补缺、返工、格式统一、P1 注册、分支提交)已在本会话生成,要点:
目录改 `correction/{品种}/`(对齐主脑 LI/);文件后缀改 `_correction_`;每板块补 4 份文件(对照表+知几json+iwencai回复+**prompt原文**);补缺 6 板块→返工 4 处→格式重命名→写 step3_cu_al_ni_sn_register.py 注册进 indicators_v1.json(append-only,_origin 标记,去重,顶层 version 用 `re.sub(r'[vV]','',ver)` 避主脑遗留 bug)。

---

## 4. 红线 / 待清

- ⚠️ `scripts/api_cache.db.bak_step3`(数据库备份)被 commit 进仓库,违反"不推 *.db"红线。应 git rm 并加 .gitignore 兜底。
- 主脑侧 si/li 数据:部分页面 HTML 硬编码 __data(如 li_3_1_5 的 229 点),不随 api_cache 刷新。需确认这是设计还是 bug;若为 bug,建页脚本应改为动态加载或重新缓存后重建。

---

## 5. 关键命令 / 路径

```bash
cd /home/ubuntu/framework-tree
# 门禁
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py
# 核验指标数
python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(list(d['indicators'].values())),d.get('version'))"
# 缓存
python3 scripts/refresh_cache.py   # 写 scripts/api_cache.db(1秒限频)
# push
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```
- 指标元数据真源: `data/indicators_v1.json`(结构 `ids:{品种:zhiji_id}`,品种键 SI=硅/LI&LC=锂)
- 时序缓存: `scripts/api_cache.db`(表 indicator_cache;推 GitHub 的只有 html/py/js/json,***.db 不入仓**)
- 铅页用描述性文件名(pb_21_price_structure.html 等),别按 si/li 的数字命名猜测。

---

## 6. 验收结论速记

| 块 | 结论 |
|---|---|
| 主脑 硅/锂 | 上线✅但需返工 R1-R6 |
| 主脑 铅/锌 | 上线✅验收通过 |
| Windows 铜铝镍锡 | 18/24 板块,缺 6+返工+未注册 |
| 红线 | api_cache.db.bak_step3 待清 |
| 上线 | 站点已收录主脑全部最新页面 |

---

## 附:给主脑的修复提示词(可直接转发)

见本会话上一轮回复,核心:修 index 缺键(3.2.1打不开)→ 修 3.1.5 挂错+频率+硬编码 → 重建 si_3_2_1 归属过滤 → 补锂指标 → 统一页脚版本 v3.46 → 每块跑三道门禁 → commit `[A-SI-LI-FIX]` 并 push。
另:清掉 scripts/api_cache.db.bak_step3 出库。
