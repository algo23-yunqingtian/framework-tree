#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_prompt.py — 词库驱动 Prompt 渲染器（通用化核心）
用法:
    python render_prompt.py --dim 库存 --variety PB \
        --subdirs "4.1交易所库存|4.2仓单|4.3社会库存|4.4工厂库存|4.5隐性·在途|4.6原料库存" \
        -o pb_库存_v19.md
    python render_prompt.py --dim 供应 --variety ZN \
        --subdirs "5.1精矿供应|5.2冶炼产量|5.3开工率|5.4进口" \
        -o zn_供应_v19.md

原理: 模板 template_v19.md 内零领域词, 全部由 dimensions/{dim}.json + varieties/{variety}.json 注入。
换维度 = 换 --dim; 换品种 = 换 --variety; 模板永不改。
"""
import argparse
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open(os.path.join(BASE, "template_v19.md"), encoding="utf-8") as f:
        return f.read()


def bullet(items):
    """['a','b'] -> '- a\n- b'（每行 '- '，无数字前缀）"""
    return "\n".join(f"- {x}" for x in items)


def render(dim, variety, subdirs):
    tpl = load_template()
    dim_conf = load_json(os.path.join(BASE, "dimensions", f"{dim}.json"))
    var_path = os.path.join(BASE, "varieties", f"{variety}.json")
    if os.path.exists(var_path):
        var_conf = load_json(var_path)
    else:
        print(f"[WARN] 品种词库 {variety}.json 不存在, 降级为空词库(仅用品种代码)")
        var_conf = {"name": variety, "industry_terms": []}

    # 品种行业词提示段（空则注入空字符串，模板内占位符消失）
    industry_terms = var_conf.get("industry_terms", [])
    variety_hint = ""
    if industry_terms:
        variety_hint = (
            "4. 指标命名尽量贴近行业惯用口径。以下为业内常见术语参考"
            "（帮助命名贴近实际，不改变筛选范围）：\n"
            + bullet(industry_terms)
        )

    # 子类列表: | 分隔 -> 每行一个
    subdir_list = "\n".join(f"{i+1}. {s}" for i, s in enumerate(subdirs.split("|")))

    subs = {
        "{品种}": var_conf["name"],
        "{维度}": dim,
        "{子类列表}": subdir_list,
        "{正例关键词}": bullet(dim_conf["positive_keywords"]),
        "{复合图主题}": bullet(dim_conf["compound_themes"]),
        "{观测用途示例}": bullet(dim_conf["usage_examples"]),
        "{边界提示}": bullet(dim_conf["boundary_tips"]),
        "{品种行业词提示}": variety_hint,
    }

    out = tpl
    for k, v in subs.items():
        if k not in out:
            print(f"[WARN] 模板中未找到占位符: {k}")
        out = out.replace(k, v)

    # 清理: 残留占位符报警
    leftovers = re.findall(r"\{[^}]+\}", out)
    if leftovers:
        print(f"[ERROR] 残留未替换占位符: {set(leftovers)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", required=True, help="维度, 对应 dimensions/{dim}.json")
    ap.add_argument("--variety", required=True, help="品种代码, 对应 varieties/{variety}.json")
    ap.add_argument("--subdirs", required=True, help="子类列表, 用 | 分隔")
    ap.add_argument("-o", "--output", required=True, help="输出文件路径")
    args = ap.parse_args()

    out = render(args.dim, args.variety, args.subdirs)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"[OK] 已渲染: {args.output}")


if __name__ == "__main__":
    main()