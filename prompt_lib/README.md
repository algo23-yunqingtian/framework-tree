# prompt_lib — 通用 Prompt 词库（Prompt Library）

**核心思想**：模板零领域词 + 维度词库 + 品种词库 = 任意组合。
换维度/换品种只换 JSON，模板永不改。

## 目录结构
```
prompt_lib/
├── template_v19.md          # 通用模板（禁止写领域词）
├── render_prompt.py         # 渲染脚本
├── dimensions/              # 维度词库（每个维度一个 JSON）
│   ├── 库存.json
│   └── 供应.json
└── varieties/               # 品种词库（每个品种一个 JSON）
    └── PB.json
```

## 用法
```bash
# 铅库存（复用已验证词库）
python render_prompt.py --dim 库存 --variety PB \
  --subdirs "4.1交易所库存|4.2仓单|4.3社会库存|4.4工厂库存|4.5隐性·在途|4.6原料库存" \
  -o ../pb_prompt/prompt_v19_PB_库存.md

# 锌供应（换维度 + 换品种）
python render_prompt.py --dim 供应 --variety ZN \
  --subdirs "4.1精矿供应|4.2冶炼产量|4.3开工率|4.4进口供应" \
  -o ../pb_prompt/prompt_v19_ZN_供应.md
```

## 新增维度（如"需求"/"价格"）
复制 `dimensions/库存.json` → `dimensions/需求.json`，改 4 个字段：
- `positive_keywords`（正例关键词）
- `compound_themes`（复合图主题）
- `usage_examples`（观测用途示例）
- `boundary_tips`（边界归属提示）

## 新增品种（如"铜 CU"/"铝 AL"）
复制 `varieties/PB.json` → `varieties/CU.json`，改 `industry_terms`（业内术语）。

## 批量渲染（一次配置，多品种×多维度全出）
```bash
# 1. 在 batch_config.json 的 tasks 数组加一条
{
  "dim": "供应", "variety": "CU",
  "subdirs": "4.1精矿供应|4.2冶炼产量|4.3开工率|4.4进口供应",
  "output": "CU_供应_v19.md"
}
# 2. 渲染
python prompt_lib/batch_render.py --config prompt_lib/batch_config.json
```

产物在 `pb_prompt/batch/`，同时生成 `tasks_manifest.json`（任务清单，供后续批量录入知几/同花顺时对照）。

**per-task 覆盖**：若某维度/品种特殊，可在 task 里加 `positive_override` / `boundary_override` / `usage_override`，直接覆盖词库注入，不影响全局词库。

## 复用验证矩阵（已实测）
| 维度 | 品种 | 状态 |
|---|---|---|
| 库存 | PB | ✅ 已投同花顺 (v19返回31指标/19图) |
| 供应 | ZN | ✅ 已渲染 (ZN词库降级, 无行业术语) |
| 需求 | PB | ✅ 已渲染 (需求词库待实测校准) |

结论：换维度=换 --dim 参数；换品种=换 --variety 参数；模板零触碰，全部由 dimensions/*.json + varieties/*.json 注入。**可直接批量跑同花顺**。

## 校验原则
1. 模板内若出现 `库存`/`交割`/`铅锭` 等具体名词 → 立即移到对应 dimensions/*.json
2. 品种词库缺失时脚本自动降级（用代码名），不阻塞
3. 模板占位符与词库字段名严格一一对应，新增占位符必须配套新增 JSON 字段