# 交接文档 v6（极简版）· 直接做 P2+P3

> 2026-09-02 主脑 | 目标：新会话一口气做完 P2、P3，无歧义

## ✅ 已完成（上轮）
- P0：merge 冲突已解决。`origin/main = df25489`，indicators **v3.49 / 1009条**，门禁 223/223 全绿，已 push
- ⚠️ fallback 已删（模型挂了直接报错）。新需求：**主模型 Qwen36_35B → 同供应商 sensenova lite6.8 互备**（不是 Qwen36！）。重配须手动改 YAML，勿用 `hermes config set`（会存成字符串毁掉链）
- ⚠️ 新会话第一步先 `git pull` + `worktree list` 看是否多 agent 并行

## P2：锂 3.2.1 产量页重建（~1h）
**真相**：7 个指标**已注册**入了 v3.49（电池级/工业级/分原料），但 `li_3_2_1.html` 还是 **v3.43 旧版 13 图**，电池级/工业级没上图。
**做法**：
```bash
cd /home/ubuntu/framework-tree
python3 scripts/build_5m_batch.py li_3_2_1    # 单页重建（args 即节点过滤）
# 验证：页面版本=v3.49、含"电池级""工业级"字样
grep -c "电池级" li_3_2_1.html
node scripts/verify_render.js li_3_2_1        # 若支持按页
python3 scripts/check_html.py                  # 全量门禁
git add li_3_2_1.html STATUS.md && git commit -m "[Txx] P2 锂3.2.1重建" && git push origin main
```
**已注册指标 id**：`ID01865204`(电池级/工业级)、`ID02226352`、`ID01707137`、`ID01707134`、`ID01707140`、`RE00033510`

## P3：全量补丢弃指标（2-3天分批）
**方法**：`/tmp/scan_drops.py`（丢弃检测脚本，仍在 /tmp 可复用；若丢从 git 历史重建）：
```bash
git show HEAD:data/indicators_v1.json > /tmp/ind_head.json  # 或直接读工作区
python3 /tmp/scan_drops.py   # divergence(198份) vs 注册 vs HTML
```
**筛选规则**（只补"可得指标"，跳过合理未注册）：
① 知几无序列 → 跳过 ② 衍生指标(月差/期限结构/占比) → 跳过 ③ 备用库跨类 → 跳过
**判断可得**：`python3 ~/.hermes/scripts/zhiji_api.py series <ID> 2015-01-01 2026-08-29` 有数据才算。
**优先级**：CU(124 未注册最严重) → ZN(264) → NI(296)；每个节点页重建 + 门禁 + push。

## 🚀 用户必答：改指标快不快？→ 快（设计目标秒级）
**核心机制**：指标元数据全在 `data/indicators_v1.json` 一行；改指标 = 改 JSON 一行 → 重建对应页：
```bash
# 改完 indicators_v1.json 后：
python3 scripts/build_5m_batch.py <节点>        # 只重建该页
python3 scripts/check_html.py && git add -A && git commit -m "[B] 指标改动" && git push origin main
```
> P4 遗留：临时把上述打包成 `regen_all.sh`（refresh_cache→重建→门禁→push 一键），实现"改一行秒上线"

## 门禁三连（提交前必跑）
```bash
python3 scripts/check_html.py        # 静态
node scripts/verify_render.js        # 渲染
python3 scripts/reclaim.py           # 格式+产物
```