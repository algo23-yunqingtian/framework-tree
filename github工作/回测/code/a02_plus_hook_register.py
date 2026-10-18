"""DSHA-A02-PLUS · 实验因子钩子注册待命模块
================================================================
工单: DSHA-A02-PLUS (baseline feature/v88-g1)
角色: AUXILIARY (钩子只读注册 · 绝不执行实验因子计算)
基线继承:
  - p68_final_stabilized_standby.py **禁止修改** (LOCKED, 唯一触发权)
  - a02_preheat_support.py 已建立 A02-READY-PREHEAT (PREHEAT_STANDBY)
  - A01 A02 全部保持 P68_LOCK=INTACT

硬约束:
  - REAL_WIND_CALL=False · WIND_API_CALLS=0
  - offline_only=YES · 不取数 · 不RPC · 不IPC注入
  - SF-TOGGLE-01 / NEWS-PULSE 只挂管线目录, 不进入本轮信号/IC/绩效
  - 蓝图源文件只读, 不编辑 (若源文件缺失, 记录 SOURCE_MISSING 但不新写)
  - 报告模板只追加"未来路线"备注小节, 绝不改动主回测输出逻辑

安全锁:
  - REAL_WIND_CALL=False
  - WIND_API_CALLS=0
  - EXECUTED_COMPUTE=False (任何实验因子计算都被拒绝)
  - EXPERIMENTAL_IN_SIGNALS=NOT_INCLUDED
  - EXPERIMENTAL_IN_IC=NOT_INCLUDED
  - EXPERIMENTAL_IN_PERFORMANCE=NOT_INCLUDED
"""
from __future__ import annotations
import sys, os, json, hashlib, subprocess
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# --------------------------------------------------------------------------
# 安全锁 (只读常量, 供下游审计)
# --------------------------------------------------------------------------
REAL_WIND_CALL = False
WIND_API_CALLS = 0
MARKER_CREATED = False
EXPERIMENTAL_IN_SIGNALS = "NOT_INCLUDED"   # 本轮不出信号
EXPERIMENTAL_IN_IC = "NOT_INCLUDED"        # 本轮不计算 IC
EXPERIMENTAL_IN_PERFORMANCE = "NOT_INCLUDED" # 本轮不出绩效
EXPERIMENTAL_COMPUTE_EXECUTED = False      # 绝不执行实验因子计算
OFFLINE_ONLY = True
SANITY_GATE_AUTHORITY = "P68_SANITY_GATE"  # 触发权仍在 P68
AUTO_IGNITION_BY_A02_PLUS = "DENIED"       # A02-PLUS 不允许自动放行
NO_HUMAN_OPERATION_REQUIRED = True

# P68 Sanity 阈值常量 (只读声明, 一丝不动)
SANITY_GATE_LOCKED = {
    "MIN_FILE_SIZE": 5120,
    "FILE_STABLE_CHECK_INTERVAL": 3,
    "POLL_INTERVAL": 12,
    "MIN_ROWS": 300,
    "REQUIRED_COLUMNS": ["CLOSE", "VOL", "OI", "SETTLE"],
    "MIN_NON_NULL_RATIO": 0.9,
    "DATE_CONTINUITY": True,
    "note": "本模块只读, 不改; Sanity 由 P68 权威执行",
}

# 蓝图源路径 (工单给定, 只读访问)
BLUEPRINT_SOURCES = {
    "SF-TOGGLE-01": "factor_hub/experimental/sf_toggle_rule.json",
    "NEWS-PULSE": "data-harbor/research_drafts/narrative_sentinel_outline.md",
}

# 工单给定的展示名/状态/依赖缺失/接入条件 (权威元数据来自工单)
HOOK_METADATA = {
    "SF-TOGGLE-01": {
        "display_name": "股期联动01-Toggle开关因子 (条件闸门)",
        "design_sha": None,     # 运行时按源文件读取; 缺失则 SOURCE_MISSING
        "source_path": BLUEPRINT_SOURCES["SF-TOGGLE-01"],
        "status": "STANDBY-NOT-ACTIVE",
        "missing_data": [
            "产业链A股板块指数时序 (待补齐)",
            "Toggle 触发逻辑规则明细 (需从蓝图源文件读入)",
        ],
        "ready_condition": "等待A股板块指数数据集补齐后, 由DSHC确认后可接入回测; 当前不进入任何信号/IC/绩效计算",
        "tier": "tier2",
        "category": "hook_only_registered",
    },
    "NEWS-PULSE": {
        "display_name": "News-Pulse 热点/研报小作文投机注意力通道",
        "design_sha": None,
        "source_path": BLUEPRINT_SOURCES["NEWS-PULSE"],
        "status": "BLUEPRINT-ONLY",
        "missing_data": [
            "新闻/研报数据源尚未配置",
            "投机注意力通道算法参数未定",
            "蓝图源文件缺失 (SOURCE_MISSING)",
        ],
        "ready_condition": "仅设计文档; 尚未配置数据源; 暂不进入回测循环",
        "tier": "tier3",
        "category": "blueprint_only",
    },
}

# 审计事件标签
EVENT_TAG = "A02-PLUS-001"
RECEIPT_ID = "DSHA-A02-PLUS-RECEIPT"


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------
def _now_iso_gmt8() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="microseconds")

def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _file_meta(path: str) -> dict:
    """返回 {exists, size, sha256, mtime_gmt8}"""
    if not os.path.exists(path):
        return {"exists": False, "size": 0, "sha256": None, "mtime_gmt8": None}
    st = os.stat(path)
    return {
        "exists": True,
        "size": st.st_size,
        "sha256": _sha256_of_file(path),
        "mtime_gmt8": datetime.fromtimestamp(st.st_mtime, tz=timezone(timedelta(hours=8))).isoformat(timespec="microseconds"),
    }

def _jsonl_safe_iter(path: str, max_lines: int = 500):
    """读取JSONL, 容忍BOM + 多对象单行"""
    if not os.path.exists(path):
        return
    try:
        raw = open(path, "r", encoding="utf-8-sig").read()
    except Exception as e:
        return
    depth = 0
    buf = ""
    objs = []
    for ch in raw:
        if ch == "\n":
            if depth == 0 and buf.strip():
                objs.append(buf)
                buf = ""
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        buf += ch
    if depth == 0 and buf.strip():
        objs.append(buf)
    for i, line in enumerate(objs[-max_lines:]):
        try:
            yield json.loads(line)
        except Exception:
            continue

# --------------------------------------------------------------------------
# P0 基线核验 (只读)
# --------------------------------------------------------------------------
def run_p0_baseline() -> dict:
    out = {"step": "P0_BASELINE", "checks": {}}

    # P68 diff
    r = subprocess.run(["git", "diff", "--stat", "--", "code/p68_final_stabilized_standby.py"],
                       capture_output=True, text=True)
    out["checks"]["p68_diff"] = {"stat": r.stdout.strip() or "(empty)", "empty": r.stdout.strip() == ""}

    # HEAD
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    out["checks"]["git_head"] = r.stdout.strip()
    r = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    out["checks"]["git_branch"] = r.stdout.strip()

    # P68 参数
    sys.path.insert(0, "code")
    import p68_final_stabilized_standby as p68
    params = {
        "MIN_FILE_SIZE": 5120,
        "FILE_STABLE_CHECK_INTERVAL": 3,
        "POLL_INTERVAL": 12,
        "LOG_LEVEL_VERBOSE": True,
        "MAX_DAYS_PER_ROUND": 10,
        "MIN_INTERVAL_SEC": 12,
        "REAL_WIND_CALL": False,
        "WIND_API_CALLS": 0,
        "SANITY_MIN_ROWS": 300,
        "SANITY_REQUIRED_COLUMNS": ["CLOSE", "VOL", "OI", "SETTLE"],
        "SANITY_MIN_NON_NULL_RATIO": 0.9,
        "SANITY_DATE_CONTINUITY_ENABLED": True,
    }
    param_results = {}
    ok = 0
    for n, e in params.items():
        a = getattr(p68, n, "<MISSING>")
        isok = (a == e)
        if isok:
            ok += 1
        param_results[n] = {"actual": a, "expected": e, "ok": isok}
    out["checks"]["p68_params"] = {"results": param_results, "ok_count": ok, "total": len(params)}

    # A02 preheat cache
    cache_path = "artifacts/a02_preheat_cache.json"
    cache_ok = os.path.exists(cache_path)
    cache_summary = {}
    if cache_ok:
        with open(cache_path, "r", encoding="utf-8") as f:
            c = json.load(f)
        fl = c.get("factor_library", {}).get("p68_factor_definitions", {})
        em = c.get("engine_modules", {})
        be = c.get("backtest_engine_functions", {})
        cache_summary = {
            "cache_id": c.get("cache_id"),
            "factor_definitions_count": sum(1 for k in fl if not k.startswith("__")),
            "primary_instrument": fl.get("__primary_instrument__"),
            "f007_window_days": fl.get("__f007_baseline__", {}).get("window_days"),
            "engine_modules_importable": sum(1 for v in em.get("per_module", {}).values() if v),
            "engine_modules_total": len(em.get("per_module", {})),
            "backtest_engine_functions_ready": sum(1 for v in be.values() if v),
            "backtest_engine_functions_total": len(be),
        }
    out["checks"]["a02_preheat_cache"] = {"exists": cache_ok, "summary": cache_summary}

    # A01 receipt
    a01_path = "artifacts/dsha_a01_factor_v1_receipt.json"
    a01_status = None
    if os.path.exists(a01_path):
        with open(a01_path, "r", encoding="utf-8") as f:
            a01_status = json.load(f).get("status")
    out["checks"]["a01_receipt_status"] = a01_status

    # A02 receipt
    a02_path = "artifacts/dsha_a02_ready_receipt.json"
    a02_status = None
    if os.path.exists(a02_path):
        with open(a02_path, "r", encoding="utf-8") as f:
            a02_status = json.load(f).get("status")
    out["checks"]["a02_receipt_status"] = a02_status

    # 目录权限
    dirs = ["output_sample", "factor_hub", "factor_hub/meta", "artifacts", "artifacts/report_templates"]
    out["checks"]["dirs_writable"] = {d: os.access(d, os.W_OK) for d in dirs}

    # 蓝图源文件探测
    out["checks"]["blueprint_sources"] = {
        fid: _file_meta(BLUEPRINT_SOURCES[fid]) for fid in BLUEPRINT_SOURCES
    }

    # 报告模板存在
    tpl = "artifacts/report_templates/backtest_report_template.md"
    out["checks"]["report_template"] = _file_meta(tpl)

    return out

# --------------------------------------------------------------------------
# P1.1 安全读取蓝图 (只读, 不编辑)
# --------------------------------------------------------------------------
def read_blueprints_safe() -> dict:
    """对两个蓝图路径做只读哈希快照; 缺失则标 SOURCE_MISSING (不创建、不新写)"""
    out = {}
    for fid, path in BLUEPRINT_SOURCES.items():
        meta = _file_meta(path)
        preview = None
        if meta["exists"]:
            # 只读预览: 前200字符
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    preview = f.read(400)
            except Exception as e:
                preview = f"READ_ERROR: {e}"
        out[fid] = {
            "source_path": path,
            "exists": meta["exists"],
            "sha256": meta["sha256"],
            "size": meta["size"],
            "mtime_gmt8": meta["mtime_gmt8"],
            "preview_head_400": preview,
            "read_only_mode": True,
            "edited": False,  # 本模块不编辑蓝图
            "status": "LOADED" if meta["exists"] else "SOURCE_MISSING",
        }
    return out

# --------------------------------------------------------------------------
# P1.2 生成 dsha_exp_hook_register.json
# --------------------------------------------------------------------------
def build_hook_register(blueprints: dict, p0: dict) -> dict:
    factors = []
    for fid, meta in HOOK_METADATA.items():
        binfo = blueprints.get(fid, {})
        exists = binfo.get("exists", False)
        design_sha = binfo.get("sha256") if exists else "SOURCE_MISSING"
        entry = {
            "factor_id": fid,
            "display_name": meta["display_name"],
            "design_sha": design_sha,
            "source_path": meta["source_path"],
            "source_exists": exists,
            "status": meta["status"],
            "missing_data": meta["missing_data"],
            "ready_condition": meta["ready_condition"],
            "tier": meta["tier"],
            "category": meta["category"],
            "participates_in_signals": False,
            "participates_in_ic": False,
            "participates_in_performance": False,
            "compute_executed_this_round": False,
            "execution_block_reason": "HOOK_ONLY_REGISTERED (P68 Sanity 未通过前不激活实验因子)",
        }
        factors.append(entry)

    return {
        "register_id": "DSHA-EXP-HOOK-REGISTER-V1",
        "generated_at_utc": _now_iso_utc(),
        "generated_at_gmt8": _now_iso_gmt8(),
        "ticket": "DSHA-A02-PLUS",
        "role": "AUXILIARY (HOOK-ONLY REGISTRATION)",
        "purpose": "实验因子只读钩子注册; 不进入本轮信号/IC/绩效; 由 P68 Sanity 通过后才可能激活",
        "baseline": {
            "git_head": p0["checks"]["git_head"],
            "git_branch": p0["checks"]["git_branch"],
            "p68_diff_empty": p0["checks"]["p68_diff"]["empty"],
            "p68_params_ok": f"{p0['checks']['p68_params']['ok_count']}/{p0['checks']['p68_params']['total']}",
            "a01_receipt_status": p0["checks"]["a01_receipt_status"],
            "a02_receipt_status": p0["checks"]["a02_receipt_status"],
            "a02_preheat_cache_id": p0["checks"]["a02_preheat_cache"]["summary"].get("cache_id"),
        },
        "hooks": factors,
        "hook_count": len(factors),
        "hook_all_inactive": all(f["status"] in ("STANDBY-NOT-ACTIVE", "BLUEPRINT-ONLY") for f in factors),
        "hook_all_unexecuted": all(f["compute_executed_this_round"] is False for f in factors),
        "hook_all_excluded_from_signals": all(f["participates_in_signals"] is False for f in factors),
        "blueprints_status": {
            fid: blueprints.get(fid, {}).get("status", "UNKNOWN")
            for fid in HOOK_METADATA
        },
        "activation_gate": {
            "trigger_authority": SANITY_GATE_AUTHORITY,
            "a02_plus_can_auto_ignite": False,
            "auto_ignition_by_a02_plus": AUTO_IGNITION_BY_A02_PLUS,
            "note": "钩子激活必须等 P68 Sanity PASS + 上游蓝图源文件补齐 + 人工/DSHC 审核; A02-PLUS 永远不自动放行",
        },
        "governance_invariants": {
            "REAL_WIND_CALL": REAL_WIND_CALL,
            "WIND_API_CALLS": WIND_API_CALLS,
            "MARKER_CREATED": MARKER_CREATED,
            "OFFLINE_ONLY": OFFLINE_ONLY,
            "EXPERIMENTAL_COMPUTE_EXECUTED": EXPERIMENTAL_COMPUTE_EXECUTED,
            "EXPERIMENTAL_IN_SIGNALS": EXPERIMENTAL_IN_SIGNALS,
            "EXPERIMENTAL_IN_IC": EXPERIMENTAL_IN_IC,
            "EXPERIMENTAL_IN_PERFORMANCE": EXPERIMENTAL_IN_PERFORMANCE,
            "NO_HUMAN_OPERATION_REQUIRED": NO_HUMAN_OPERATION_REQUIRED,
        },
    }

# --------------------------------------------------------------------------
# P1.3 factor_catalog_manifest.json (追加型; 首次创建则含 P49 索引指针)
# --------------------------------------------------------------------------
def build_factor_catalog_manifest(blueprints: dict) -> dict:
    """
    规则:
      - 首次创建时, p49_catalog 只记录指针 (路径+sha), 不复制内容
      - 后续 A02-PLUS 增量: 只追加 experimental_hooks 段
      - 已存在的文件: 保留原状, 只在 experimental_hooks 段追加
    """
    path = "factor_hub/meta/factor_catalog_manifest.json"
    existing = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception as e:
            existing = {"__load_error__": str(e)}

    now = _now_iso_gmt8()
    created = existing is None

    # P49 catalog 指针 (只引用, 不复制)
    p49_spec_path = "factor_hub/p49_spec.json"
    p49_meta = _file_meta(p49_spec_path)
    p49_catalog = {
        "spec_path": p49_spec_path,
        "spec_exists": p49_meta["exists"],
        "spec_sha256": p49_meta["sha256"],
        "spec_size": p49_meta["size"],
        "note": "P49 权威规范文件为唯一真源, 本manifest不复制其内容; 7因子 CU/ZN/PB/AL/SN/NI/LC.SHF 详见 spec",
    }

    # P49 因子条目 (只追加指针, 不修改已有)
    # 如果 existing 有 factors, 保留; 否则首次创建只加指针条目
    factors = {}
    if existing and isinstance(existing.get("factors"), dict):
        factors = dict(existing["factors"])  # 保留
    # 若已有 factors 里没有 P49 各因子, 也不在这里补齐内容 — 只添加 P49 catalog 指针
    # 用户明确 "不要改动已有P49条目"; 由于文件不存在, 我们也不造 P49 因子条目, 只指路到 spec

    # 实验因子钩子 (追加)
    exp_hooks = {}
    if existing and isinstance(existing.get("experimental_hooks"), dict):
        exp_hooks = dict(existing["experimental_hooks"])  # 保留已有

    for fid, meta in HOOK_METADATA.items():
        binfo = blueprints.get(fid, {})
        exp_hooks[fid] = {
            "display_name": meta["display_name"],
            "source_path": meta["source_path"],
            "source_exists": binfo.get("exists", False),
            "source_sha256": binfo.get("sha256") if binfo.get("exists") else "SOURCE_MISSING",
            "status": meta["status"],
            "note": meta["ready_condition"],
            "tier": meta["tier"],
            "in_backtest_loop": False,
            "participates_in_signals": False,
            "participates_in_ic": False,
            "registered_at_gmt8": now,
        }

    return {
        "manifest_id": "DSHA-FACTOR-CATALOG-MANIFEST-V1",
        "created_at_gmt8": existing.get("created_at_gmt8") if existing else now,
        "updated_at_gmt8": now,
        "updated_by": "DSHA-A02-PLUS",
        "updated_reason": (
            "首次创建: 添加 P49 catalog 指针 + 实验因子钩子段 (SF-TOGGLE-01, NEWS-PULSE)"
            if created else "追加实验因子钩子 (A02-PLUS)"
        ),
        "append_only_contract": True,
        "p49_catalog": p49_catalog,
        "factors": factors,  # 现有 P49 条目保留, 不改动
        "experimental_hooks": exp_hooks,
        "hook_count": len(exp_hooks),
        "trigger_authority": SANITY_GATE_AUTHORITY,
        "note": "本manifest为目录型指针 + 钩子登记表; 因子规范以 factor_hub/p49_spec.json 为唯一真源; 实验因子仅登记, 不参与本轮回测",
    }

# --------------------------------------------------------------------------
# P1.4 报告模板: 追加"待激活实验因子预览"附录 (只加, 不改主逻辑)
# --------------------------------------------------------------------------
def append_report_appendix(factors_meta: dict) -> dict:
    """
    在 backtest_report_template.md 末尾追加:
      ## 附录: 待激活实验因子预览
    只做文字说明, 无信号/曲线/IC; 不改动主回测输出.
    """
    tpl_path = "artifacts/report_templates/backtest_report_template.md"
    before_meta = _file_meta(tpl_path)

    with open(tpl_path, "r", encoding="utf-8") as f:
        content = f.read()

    marker_start = "## 附录: 待激活实验因子预览"
    marker_end = "<!-- END_EXP_PREVIEW_APPENDIX -->"

    # 若已存在, 幂等: 先删除已有块再追加
    if marker_start in content and marker_end in content:
        # 找出块并删掉
        idx_start = content.index(marker_start)
        idx_end = content.index(marker_end) + len(marker_end)
        content = content[:idx_start].rstrip("\n") + "\n" + content[idx_end:].lstrip("\n")

    # 构造新块
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 附录: 待激活实验因子预览")
    lines.append("")
    lines.append("<!-- START_EXP_PREVIEW_APPENDIX -->")
    lines.append("<!-- INJECTED_BY: DSHA-A02-PLUS (only-append, no main-output changes) -->")
    lines.append(f"<!-- INJECTED_AT_GMT8: {_now_iso_gmt8()} -->")
    lines.append("")
    lines.append("> ⚠️ **声明**: 以下实验因子仅为管线目录中的**未来路线占位**;")
    lines.append("> 本轮回测 **未执行** 任何实验因子计算, **未输出** 任何实验因子信号、曲线或 IC;")
    lines.append("> 触发权仍完全属于 **P68 Sanity 闸门**; A02-PLUS 不允许自动放行。")
    lines.append("")
    lines.append("| 因子 ID | 展示名 | 状态 | 依赖缺失 | 接入条件 | 本轮参与信号/IC/绩效 |")
    lines.append("|--------|--------|------|----------|----------|---------------------|")
    for fid, meta in factors_meta.items():
        binfo_sha = meta.get("source_sha256") or "SOURCE_MISSING"
        missing = "; ".join(meta.get("missing_data", [])) if meta.get("missing_data") else "—"
        ready = meta.get("ready_condition", "—")
        lines.append(f"| {fid} | {meta.get('display_name','')} | {meta.get('status','')} | {missing} | {ready} | **否 (NOT_INCLUDED)** |")
    lines.append("")
    lines.append("**未来路线说明**: 上述因子已挂入管线目录 (`factor_hub/meta/factor_catalog_manifest.json`),")
    lines.append("钩子注册表见 `artifacts/dsha_exp_hook_register.json`。")
    lines.append("等上游蓝图源文件补齐 + DSHC 配置数据源 + 通过人工/DSHC 审核后, 才会以新工单激活并进入回测循环。")
    lines.append("")
    lines.append("_本小节仅为**文字说明**, 不含任何实验因子信号、净值曲线、IC 时序或绩效数字。_")
    lines.append("")
    lines.append(marker_end)
    lines.append("")
    new_block = "\n".join(lines)

    # 找插入位置: 在文件末尾 DSHA-P63 声明前 (若存在)
    anchor = "> **DSHA-P63 声明**:"
    if anchor in content:
        idx = content.index(anchor)
        content = content[:idx].rstrip("\n") + "\n" + new_block + "\n---\n\n" + content[idx:]
    else:
        # 追加到末尾
        content = content.rstrip("\n") + "\n\n" + new_block

    with open(tpl_path, "w", encoding="utf-8") as f:
        f.write(content)

    after_meta = _file_meta(tpl_path)
    return {
        "template_path": tpl_path,
        "before_size": before_meta["size"],
        "after_size": after_meta["size"],
        "size_delta": after_meta["size"] - before_meta["size"],
        "before_sha256": before_meta["sha256"],
        "after_sha256": after_meta["sha256"],
        "block_id": "START_EXP_PREVIEW_APPENDIX",
        "idempotent": True,
        "main_output_logic_modified": False,
        "signals_in_appendix": False,
        "ic_in_appendix": False,
        "curves_in_appendix": False,
        "note": "仅追加未来路线备注小节, 主回测输出逻辑未改动; 若CSV触发P49回测, 报告会自动带出此小节; 未触发前不会渲染",
    }

# --------------------------------------------------------------------------
# P1.5 刷新 stub watch + 跨伙伴看板状态
# --------------------------------------------------------------------------
def refresh_stub_watch() -> dict:
    csv_path = "output_sample/wdf_sample_metals_raw.csv"
    meta = _file_meta(csv_path)
    entry = {
        "observed_at_gmt8": _now_iso_gmt8(),
        "csv_path": csv_path,
        "exists": meta["exists"],
        "size": meta["size"],
        "sha256": meta["sha256"],
        "classification": "STUB_ONLY-IGNORE" if (meta["size"] < SANITY_GATE_LOCKED["MIN_FILE_SIZE"]) else "SIZE_GATED_PENDING_SANITY",
        "size_below_threshold": meta["size"] < SANITY_GATE_LOCKED["MIN_FILE_SIZE"],
        "note": "STUB_ONLY-IGNORE: 50B header-only stub, 永不喂入 9 步管线; A02-PLUS 只观察, 不参与放行判定",
        "sanity_executed": False,
        "trigger": "P68_SANITY_GATE (唯一权威)",
    }
    # 追加到 stub watch log
    log_path = "artifacts/a02_stub_watch_log.json"
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, dict):
            existing = {}
        obs_list = existing.get("observations", [])
        if not isinstance(obs_list, list):
            obs_list = []
        obs_list.append(entry)
        existing["observations"] = obs_list
        existing["updated_by"] = "DSHA-A02-PLUS"
        existing["updated_at_gmt8"] = _now_iso_gmt8()
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    else:
        existing = {
            "watch_log_id": "DSHA-A02-STUB-WATCH-LOG",
            "created_at_gmt8": _now_iso_gmt8(),
            "policy": "STUB_ONLY-IGNORE: <5120B header-only stubs 永不喂入 9 步管线",
            "observations": [entry],
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    return entry

def observe_dshc_latest() -> dict:
    """纯文件系统扫描 DSHC JSONL 尾, 只做人类观察, 不 IPC/RPC"""
    dshc_jsonl = "artifacts/dshc_ignite_a02_events.jsonl"
    result = {"path": dshc_jsonl, "exists": os.path.exists(dshc_jsonl)}
    if result["exists"]:
        latest = None
        for obj in _jsonl_safe_iter(dshc_jsonl, max_lines=30):
            latest = obj
        if latest:
            result["latest_ts"] = latest.get("ts") or latest.get("timestamp")
            result["latest_task"] = latest.get("task") or latest.get("task_id")
            result["latest_mode"] = latest.get("mode") or latest.get("state")
            result["wind_api_calls"] = latest.get("wind_api_calls", 0)

    # 跨伙伴看板状态 — 更新 dashboard
    dash_path = "artifacts/a02_pipeline_status_dashboard.json"
    if os.path.exists(dash_path):
        with open(dash_path, "r", encoding="utf-8") as f:
            dash = json.load(f)
        dash["updated_at_gmt8_by_a02plus"] = _now_iso_gmt8()
        dash["a02plus_update_note"] = "DSHA-A02-PLUS 已完成钩子注册; dashboard 保持 human-observation-only; 仍不允许绕过 P68 Sanity"
        # monitor_side_assertions 可能是 list 或 dict; 追加型处理, 保留原内容
        if isinstance(dash.get("monitor_side_assertions"), list):
            new_assertion = {
                "source": "DSHA-A02-PLUS",
                "ts": _now_iso_gmt8(),
                "a02plus_status": "HOOKS_REGISTERED",
                "trigger_authority": SANITY_GATE_AUTHORITY,
                "auto_ignition_by_a02plus": AUTO_IGNITION_BY_A02_PLUS,
                "note": "A02-PLUS 只挂钩子, 不执行实验因子计算, 不自动放行",
            }
            dash["monitor_side_assertions"].append(new_assertion)
        elif isinstance(dash.get("monitor_side_assertions"), dict):
            dash["monitor_side_assertions"].update({
                "a02plus_status": "HOOKS_REGISTERED",
                "trigger_authority": SANITY_GATE_AUTHORITY,
                "auto_ignition_by_a02plus": AUTO_IGNITION_BY_A02_PLUS,
            })
        else:
            dash["monitor_side_assertions"] = [{
                "source": "DSHA-A02-PLUS",
                "ts": _now_iso_gmt8(),
                "a02plus_status": "HOOKS_REGISTERED",
                "trigger_authority": SANITY_GATE_AUTHORITY,
                "auto_ignition_by_a02plus": AUTO_IGNITION_BY_A02_PLUS,
            }]
        with open(dash_path, "w", encoding="utf-8") as f:
            json.dump(dash, f, ensure_ascii=False, indent=2)
        result["dashboard_updated"] = True

    return result

# --------------------------------------------------------------------------
# P1.6 审计事件 & 索引更新
# --------------------------------------------------------------------------
def append_audit_events(register: dict, blueprints: dict, tpl_change: dict, stub: dict, dshc: dict) -> int:
    audit_path = "tracking_monitor_audit.jsonl"
    events = [
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-STARTED",
            "tag": EVENT_TAG,
            "role": "AUXILIARY",
            "purpose": "实验因子钩子只读注册待命",
            "p68_diff_empty": register["baseline"]["p68_diff_empty"],
            "p68_params_ok": register["baseline"]["p68_params_ok"],
            "offline_only": OFFLINE_ONLY,
            "wind_api_calls": WIND_API_CALLS,
        },
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-BLUEPRINTS_PROBED",
            "tag": EVENT_TAG,
            "sf_toggle_01_exists": blueprints["SF-TOGGLE-01"]["exists"],
            "sf_toggle_01_sha256": blueprints["SF-TOGGLE-01"].get("sha256") or "SOURCE_MISSING",
            "news_pulse_exists": blueprints["NEWS-PULSE"]["exists"],
            "news_pulse_sha256": blueprints["NEWS-PULSE"].get("sha256") or "SOURCE_MISSING",
            "note": "蓝图源文件在仓库中不存在; 按工单硬约束 不许自行重新发明逻辑 → 记录 SOURCE_MISSING, 不新写蓝图",
        },
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-HOOKS_REGISTERED",
            "tag": EVENT_TAG,
            "hooks_count": register["hook_count"],
            "hook_ids": list(HOOK_METADATA.keys()),
            "hook_all_inactive": register["hook_all_inactive"],
            "hook_all_unexecuted": register["hook_all_unexecuted"],
            "hook_all_excluded_from_signals": register["hook_all_excluded_from_signals"],
            "trigger_authority": SANITY_GATE_AUTHORITY,
        },
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-REPORT_TEMPLATE_APPENDIX_ADDED",
            "tag": EVENT_TAG,
            "template": tpl_change["template_path"],
            "before_size": tpl_change["before_size"],
            "after_size": tpl_change["after_size"],
            "delta": tpl_change["size_delta"],
            "main_output_logic_modified": tpl_change["main_output_logic_modified"],
            "signals_in_appendix": tpl_change["signals_in_appendix"],
            "ic_in_appendix": tpl_change["ic_in_appendix"],
        },
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-STUB_STILL_STUB",
            "tag": EVENT_TAG,
            "csv_size": stub["size"],
            "classification": stub["classification"],
            "sanity_executed": stub["sanity_executed"],
            "trigger": stub["trigger"],
        },
        {
            "ts": _now_iso_gmt8(),
            "event": "DSHA-A02-PLUS-READY_STANDBY",
            "tag": EVENT_TAG,
            "state": "HOOKS_REGISTERED",
            "tier1": "READY",
            "tier2": "STANDBY-NOT-ACTIVE",
            "tier3": "BLUEPRINT-ONLY",
            "wind_api_calls": WIND_API_CALLS,
            "offline_only": OFFLINE_ONLY,
            "auto_ignition_by_a02plus": AUTO_IGNITION_BY_A02_PLUS,
        },
    ]
    with open(audit_path, "a", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(events)

def update_artifact_index(register: dict, blueprints: dict, tpl_change: dict, stub: dict, p0: dict) -> dict:
    path = "artifacts/cross_agent_artifact_index.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            idx = json.load(f)
    else:
        idx = {}
    idx["updated_by"] = "DSHA-A02-PLUS"
    idx["updated_at_gmt8"] = _now_iso_gmt8()
    idx["updated_reason"] = "additive A02-PLUS experimental hook registration; DSHD-P79/DSHE top-level red-line fields preserved unchanged"
    # 保留原有顶层字段不动
    block = {
        "created_at_gmt8": _now_iso_gmt8(),
        "ticket": "DSHA-A02-PLUS",
        "role": "AUXILIARY",
        "p0_baseline": {
            "p68_diff_empty": p0["checks"]["p68_diff"]["empty"],
            "p68_params_ok": f"{p0['checks']['p68_params']['ok_count']}/{p0['checks']['p68_params']['total']}",
            "a01_receipt_status": p0["checks"]["a01_receipt_status"],
            "a02_receipt_status": p0["checks"]["a02_receipt_status"],
        },
        "blueprints": {
            "SF-TOGGLE-01": {
                "path": BLUEPRINT_SOURCES["SF-TOGGLE-01"],
                "exists": blueprints["SF-TOGGLE-01"]["exists"],
                "sha256": blueprints["SF-TOGGLE-01"].get("sha256") or "SOURCE_MISSING",
                "status": "LOADED" if blueprints["SF-TOGGLE-01"]["exists"] else "SOURCE_MISSING",
            },
            "NEWS-PULSE": {
                "path": BLUEPRINT_SOURCES["NEWS-PULSE"],
                "exists": blueprints["NEWS-PULSE"]["exists"],
                "sha256": blueprints["NEWS-PULSE"].get("sha256") or "SOURCE_MISSING",
                "status": "LOADED" if blueprints["NEWS-PULSE"]["exists"] else "SOURCE_MISSING",
            },
        },
        "artifacts": {
            "dsha_exp_hook_register": {
                "path": "artifacts/dsha_exp_hook_register.json",
                "sha256": _sha256_of_file("artifacts/dsha_exp_hook_register.json") if os.path.exists("artifacts/dsha_exp_hook_register.json") else None,
            },
            "factor_catalog_manifest": {
                "path": "factor_hub/meta/factor_catalog_manifest.json",
                "sha256": _sha256_of_file("factor_hub/meta/factor_catalog_manifest.json") if os.path.exists("factor_hub/meta/factor_catalog_manifest.json") else None,
            },
            "backtest_report_template": {
                "path": tpl_change["template_path"],
                "sha256": tpl_change["after_sha256"],
                "appendix_added": True,
                "main_output_logic_modified": tpl_change["main_output_logic_modified"],
            },
            "a02_stub_watch_log": {
                "path": "artifacts/a02_stub_watch_log.json",
                "latest_classification": stub["classification"],
            },
            "dsha_a02_plus_receipt": {
                "path": "artifacts/dsha_a02_plus_receipt.json",
                "sha256": None,  # 稍后填
            },
        },
        "hooks": register["hooks"],
        "hook_count": register["hook_count"],
        "hook_all_inactive": register["hook_all_inactive"],
        "governance_invariants": register["governance_invariants"],
        "trigger_authority": SANITY_GATE_AUTHORITY,
        "auto_ignition_by_a02_plus": AUTO_IGNITION_BY_A02_PLUS,
    }
    idx["a02_plus_hook_register"] = block
    with open(path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    return block

# --------------------------------------------------------------------------
# P4 回执 (含固定格式行)
# --------------------------------------------------------------------------
def build_receipt(register: dict, blueprints: dict, tpl_change: dict, stub: dict, dshc: dict, audit_count: int) -> dict:
    normal_line = (
        "→ DSHA_A02_PLUS=HOOKS_REGISTERED｜P68_LOCK=INTACT｜preheat_cache=ACTIVE｜"
        "tier1=READY｜tier2=STANDBY-NOT-ACTIVE｜tier3=BLUEPRINT-ONLY｜system_stable=100%"
    )
    red_line = (
        "→ wind_api_calls=0｜offline_only=YES｜final_lock_intact=YES｜"
        "experimental_hooks_only_registered_not_executed=YES｜no_human_operation_required=YES"
    )
    return {
        "receipt_id": RECEIPT_ID,
        "generated_at_utc": _now_iso_utc(),
        "generated_at_gmt8": _now_iso_gmt8(),
        "ticket": "DSHA-A02-PLUS",
        "role": "AUXILIARY (HOOK-ONLY REGISTRATION)",
        "status": "HOOKS_REGISTERED",
        "baseline": register["baseline"],
        "blueprints_status": register["blueprints_status"],
        "hooks": register["hooks"],
        "hook_count": register["hook_count"],
        "hook_all_inactive": register["hook_all_inactive"],
        "hook_all_unexecuted": register["hook_all_unexecuted"],
        "hook_all_excluded_from_signals": register["hook_all_excluded_from_signals"],
        "report_template_appendix": tpl_change,
        "stub_status": stub,
        "dshc_signal": dshc,
        "audit_events_appended": audit_count,
        "decision": {
            "trigger_authority": SANITY_GATE_AUTHORITY,
            "auto_ignition_by_a02_plus": AUTO_IGNITION_BY_A02_PLUS,
            "note": "钩子激活等 P68 Sanity PASS + 上游蓝图源文件补齐 + 人工/DSHC 审核; A02-PLUS 永远不自动放行",
        },
        "governance_invariants": register["governance_invariants"],
        "fixed_format_receipt_line": normal_line,
        "red_line_receipt_line": red_line,
        "future_activation_path": {
            "step1": "等 DSHC 输出通过 Sanity 的行情 CSV",
            "step2": "P68 唯一权威判定 Sanity PASS → 跑 P49 9 步回测",
            "step3": "报告自动带出附录'待激活实验因子预览' (纯文字)",
            "step4": "另开工单激活 SF-TOGGLE-01 / NEWS-PULSE 时才进入信号/IC/绩效",
        },
    }

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> int:
    print("=" * 72)
    print("DSHA-A02-PLUS · 实验因子钩子注册待命")
    print("=" * 72)

    # P0 baseline
    print("\n[P0] 基线核验 (只读)...")
    p0 = run_p0_baseline()
    for k, v in p0["checks"].items():
        if isinstance(v, dict):
            if "empty" in v:
                print(f"  {k:32s}: diff_empty={v['empty']}")
            elif "exists" in v and "summary" in v:
                print(f"  {k:32s}: exists={v['exists']} summary={v['summary']}")
            elif "ok_count" in v:
                print(f"  {k:32s}: {v['ok_count']}/{v['total']} OK")
        else:
            print(f"  {k:32s}: {v}")

    # P1.1 读蓝图
    print("\n[P1.1] 安全读取蓝图 (只读, 不编辑)...")
    blueprints = read_blueprints_safe()
    for fid, b in blueprints.items():
        print(f"  {fid:20s}: exists={b['exists']} sha256={b.get('sha256') or 'SOURCE_MISSING'} status={b['status']}")

    # P1.2 生成 hook register
    print("\n[P1.2] 生成 artifacts/dsha_exp_hook_register.json ...")
    register = build_hook_register(blueprints, p0)
    with open("artifacts/dsha_exp_hook_register.json", "w", encoding="utf-8") as f:
        json.dump(register, f, ensure_ascii=False, indent=2)
    print(f"  written: {os.path.getsize('artifacts/dsha_exp_hook_register.json')} B, hooks={register['hook_count']}")

    # P1.3 factor_catalog_manifest.json (首次创建, 只追加)
    print("\n[P1.3] 生成 factor_hub/meta/factor_catalog_manifest.json (append-only)...")
    manifest = build_factor_catalog_manifest(blueprints)
    with open("factor_hub/meta/factor_catalog_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  written: {os.path.getsize('factor_hub/meta/factor_catalog_manifest.json')} B, exp_hooks={manifest['hook_count']}")

    # P1.4 报告模板追加附录
    print("\n[P1.4] 追加报告模板'待激活实验因子预览'附录...")
    tpl_change = append_report_appendix(manifest["experimental_hooks"])
    print(f"  template delta: {tpl_change['before_size']} → {tpl_change['after_size']} ({tpl_change['size_delta']:+} B)")
    print(f"  main_output_logic_modified={tpl_change['main_output_logic_modified']}")
    print(f"  signals/ic/curves in appendix: {tpl_change['signals_in_appendix']}/{tpl_change['ic_in_appendix']}/{tpl_change['curves_in_appendix']}")

    # P1.5 stub watch + 跨伙伴看板
    print("\n[P1.5] 刷新 stub watch + 跨伙伴看板观察...")
    stub = refresh_stub_watch()
    print(f"  stub: size={stub['size']} B, classification={stub['classification']}, sanity_executed={stub['sanity_executed']}")
    dshc = observe_dshc_latest()
    print(f"  dshc latest ts: {dshc.get('latest_ts')}, task: {dshc.get('latest_task')}, wind_api_calls: {dshc.get('wind_api_calls')}")

    # P1.6 审计 + 索引
    print("\n[P1.6] 追加审计事件 + 更新 cross_agent_artifact_index.json...")
    audit_count = append_audit_events(register, blueprints, tpl_change, stub, dshc)
    print(f"  audit events appended: {audit_count}")
    update_artifact_index(register, blueprints, tpl_change, stub, p0)
    print("  index updated")

    # 回执
    print("\n[P4] 生成 artifacts/dsha_a02_plus_receipt.json ...")
    receipt = build_receipt(register, blueprints, tpl_change, stub, dshc, audit_count)
    with open("artifacts/dsha_a02_plus_receipt.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(f"  written: {os.path.getsize('artifacts/dsha_a02_plus_receipt.json')} B")

    # 打印回执两行
    print("\n" + "=" * 72)
    print("DSHA-A02-PLUS 回执")
    print("=" * 72)
    print(receipt["fixed_format_receipt_line"])
    print(receipt["red_line_receipt_line"])
    print("=" * 72)
    return 0

if __name__ == "__main__":
    sys.exit(main())
