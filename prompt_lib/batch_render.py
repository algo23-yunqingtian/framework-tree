#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_render.py — 批量渲染 Prompt（一次配置，全量生成）
用法:
    python prompt_lib/batch_render.py --config prompt_lib/batch_config.json
    python prompt_lib/batch_render.py --config prompt_lib/batch_config.json --dry-run   # 只预览不写

config JSON 结构:
{
  "output_dir": "../pb_prompt/batch",
  "tasks": [
    {
      "dim": "库存", "variety": "PB",
      "subdirs": "4.1交易所库存|4.2仓单|4.3社会库存|4.4工厂库存|4.5隐性·在途",
      "output": "PB_库存_v19.md"
    },
    {
      "dim": "供应", "variety": "ZN",
      "subdirs": "4.1精矿供应|4.2冶炼产量|4.3开工率|4.4进口供应",
      "output": "ZN_供应_v19.md"
    }
  ]
}

注意: 子类列表若维度词库的边界提示与子类不匹配, 人工在 config 里覆盖:
  "boundary_override": ["自定义边界提示行1", "..."],
  或 "positive_override": ["自定义正例关键词..."]

产物: 每个 task 生成一个 .md, 同时生成 tasks_manifest.json (任务清单, 供后续批量录入知几时对照)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_prompt import render, bullet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="批量配置 JSON 路径")
    ap.add_argument("--dry-run", action="store_true", help="只打印任务清单不写文件")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    output_dir = cfg.get("output_dir", ".")
    tasks = cfg["tasks"]
    print(f"[INFO] 共 {len(tasks)} 个任务, 输出目录: {output_dir}")

    manifest = []
    for i, t in enumerate(tasks, 1):
        dim = t["dim"]
        variety = t["variety"]
        subdirs = t["subdirs"]
        output = t["output"]
        print(f"\n[{i}/{len(tasks)}] {variety}·{dim} -> {output}")
        print(f"    子类: {subdirs.split('|')}")

        if args.dry_run:
            manifest.append({"task": i, "variety": variety, "dim": dim, "output": output, "subdirs": subdirs.split("|")})
            continue

        # 渲染（支持 per-task 覆盖词库）
        tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_v19.md")
        with open(tpl_path, encoding="utf-8") as f:
            tpl = f.read()

        out = render(dim, variety, subdirs)

        # 可选覆盖: 正例关键词 / 边界提示 / 观测用途
        if t.get("positive_override"):
            start = out.index("**规则4：允许指标类型（正例关键词）**")
            end = out.index("**规则5：图表形态")
            out = out[:start] + "**规则4：允许指标类型（正例关键词）**\n" + bullet(t["positive_override"]) + "\n" + out[end:]
        if t.get("boundary_override"):
            start = out.index("**规则7：边界归属提示（防越界）**")
            end = out.index("【工作方法】")
            out = out[:start] + "**规则7：边界归属提示（防越界）**\n" + bullet(t["boundary_override"]) + "\n" + out[end:]
        if t.get("usage_override"):
            start = out.index("参考示例：")
            end = out.index("【工作方法】" if "【工作方法】" in out[start:] else "**规则7")
            seg = out[start:end]
            new_seg = "参考示例：\n" + bullet(t["usage_override"]) + "\n"
            out = out[:start] + new_seg + out[end:]

        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_dir, output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out)
        manifest.append({"task": i, "variety": variety, "dim": dim, "output": output,
                         "subdirs": subdirs.split("|"), "path": out_path})

    # 任务清单落盘
    manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_dir, "tasks_manifest.json")
    if not args.dry_run:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 任务清单: {manifest_path if not args.dry_run else '(dry-run 不写)'}")


if __name__ == "__main__":
    main()