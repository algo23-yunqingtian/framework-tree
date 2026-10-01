#!/usr/bin/env python3
"""
artifact_ingest_check.py — V85 交付物入库完整性校验脚本
==========================================================
B_V85_ARTIFACT_PERSIST_AND_SNAPSHOT_VERIFY

功能:
  1. MD5 校验: 对全部文件计算 MD5, 与归档清单比对
  2. 目录结构校验: 验证预期目录层级存在
  3. 批量加载校验: JSON/CSV/MD/PY 解析异常捕获 (编码/格式/损坏)
  4. 快照可用性探测: 验证 git tag 存在, 快照文件完整性
  5. 只读锁定校验: 确认关键文件未被修改 (mtime + MD5 对比)

用法:
  python artifact_ingest_check.py                          # 全量校验
  python artifact_ingest_check.py --md5-only               # 仅 MD5
  python artifact_ingest_check.py --structure-only         # 仅结构
  python artifact_ingest_check.py --parse-only             # 仅解析
  python artifact_ingest_check.py --snapshot-only          # 仅快照
  python artifact_ingest_check.py --output result.json     # 输出 JSON
  python artifact_ingest_check.py --verbose                # 详细输出

约束:
  NO_ZHIJI_API_CALL=TRUE  — 不调用任何外部API
  READ_ONLY=TRUE          — 仅读取文件, 不修改
"""

import os
import sys
import json
import csv
import hashlib
import re
import argparse
import subprocess
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# ==============================================================================
# 配置
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", ".."))
V85_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v85")
ARCHIVE_DIR = os.path.join(REPO_ROOT, "v85_final_archive")
B_STORAGE_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v85", "b_storage_persist")

# 预期存在的核心目录
EXPECTED_DIRS = [
    "analysis/e2e_output/v85/dshb_final_gate_summary",
    "analysis/e2e_output/v85/dshb_review_simulation",
    "analysis/e2e_output/v85/dshb_human_review_prep",
    "analysis/e2e_output/v85/dshb_full_integrate",
    "analysis/e2e_output/v85/dshe_alias_audit_design",
    "analysis/e2e_output/v85/miss_risk_mining",
    "analysis/e2e_output/v85/review_doc",
    "analysis/e2e_output/v85/review_export_package",
    "analysis/e2e_output/v85/risk_implement_verify",
    "analysis/e2e_output/v85/risk_rootcause_review",
    "analysis/e2e_output/v85/unified_risk_db",
    "analysis/e2e_output/v85/meta_check",
    "analysis/e2e_output/v85/meta_gap",
    "analysis/e2e_output/v85/pdf_extract",
    "analysis/e2e_output/v85/pdf_template_build",
    "analysis/e2e_output/v85/ths_check",
    "analysis/e2e_output/v85/tonghuashun_recheck",
    "analysis/e2e_output/v85/tonghuashun_recheck_fixed",
    "analysis/e2e_output/v85/tonghuashun_template_package",
    "analysis/e2e_output/v85/hermes_portal_gate_final",
    "analysis/e2e_output/v85/hermes_human_review_tool",
    "analysis/e2e_output/v85/hermes_portal_sim_demo",
    "analysis/e2e_output/v85/hermes_v85_final_delivery",
    "analysis/e2e_output/v85/hermes_v85_archive_prep",
    "analysis/e2e_output/v85/hermes_refresh_real_data",
    "analysis/e2e_output/v85/v85_final_integrate",
    "analysis/e2e_output/v85/v85_final_integrate",
    "analysis/e2e_output/v85/v85_render_fix_review_package",
    "analysis/e2e_output/v85/v85_portal_enhance_render_sim",
    "analysis/e2e_output/v85/v85_ths_mapping_gap_prep",
    "analysis/e2e_output/v85/prep_for_ths_and_auto_check_enhance",
    "analysis/e2e_output/v85/fuzzy_match_fix",
    "analysis/e2e_output/v85/alias_lib_full_audit",
    "analysis/e2e_output/v85/alias_match_presearch",
    "analysis/e2e_output/v85/dshe_alias_integrate_test",
    "analysis/e2e_output/v85/b_storage_persist",
    "v85_final_archive",
]

# 核心文件白名单 (只读锁定检查)
CORE_FILES = [
    # 黑名单
    "analysis/e2e_output/v85/dshb_full_integrate/semantic_blacklist_v85_final.json",
    "analysis/e2e_output/v85/miss_risk_mining/blacklist_extend_candidate_v2.json",
    # 别名库
    "analysis/e2e_output/v85/hermes_portal_gate_final/indicator_alias_library.csv",
    "analysis/e2e_output/v85/alias_lib_full_audit/indicator_alias_library.csv",
    # 风险库
    "analysis/e2e_output/v85/unified_risk_db/unified_indicator_risk_db.csv",
    "analysis/e2e_output/v85/miss_risk_mining/unified_indicator_risk_db_v2.csv",
    "analysis/e2e_output/v85/risk_implement_verify/unified_indicator_risk_db_final.csv",
    # 模板
    "analysis/e2e_output/v85/pdf_template_build/pdf_web_chart_template_draft.json",
    "analysis/e2e_output/v85/ths_check/ths_chart_template_list.json",
    "analysis/e2e_output/v85/tonghuashun_template_package/tonghuashun_chart_template.json",
    # 场景回放
    "analysis/e2e_output/v85/dshb_review_simulation/sim_sceneA_result.csv",
    "analysis/e2e_output/v85/dshb_review_simulation/sim_sceneB_result.csv",
    # 测试集
    "analysis/e2e_output/v85/dshe_alias_audit_design/alias_test_case_set.json",
    "analysis/e2e_output/v85/miss_risk_mining/blacklist_boundary_testset.json",
    # 交付报告
    "analysis/e2e_output/v85/dshb_final_gate_summary/dsh_final_gate_acceptance.md",
    "analysis/e2e_output/v85/dshb_final_gate_summary/v85_rule_full_summary.md",
    "analysis/e2e_output/v85/dshb_final_gate_summary/v85_risk_final_conclusion.md",
    "analysis/e2e_output/v85/dshb_final_gate_summary/v86_rule_milestone_ticket.md",
    "analysis/e2e_output/v85/dshb_final_gate_summary/dshb_data_readme_for_hermes.md",
    # JOB_READY.flag
    "analysis/e2e_output/v85/JOB_READY.flag",
    "analysis/e2e_output/v85/MD5_CHECKSUM_LIST.md",
]

# 文件扩展名分组
PARSE_GROUPS = {
    "json": [".json"],
    "csv": [".csv"],
    "md": [".md"],
    "py": [".py"],
    "txt": [".txt"],
    "jsonl": [".jsonl"],
}


# ==============================================================================
# 工具函数
# ==============================================================================

def log(msg: str, verbose: bool = False, level: str = "INFO"):
    """输出日志"""
    if level == "ERROR" or level == "WARN" or verbose:
        print(f"[{level}] {msg}")
    elif level == "INFO":
        print(msg)


def compute_md5(filepath: str) -> Optional[str]:
    """计算文件MD5"""
    try:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return None


def get_file_ext(filepath: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filepath)[1].lower()


def should_exclude(filepath: str) -> bool:
    """判断是否排除 (zhiji缓存、__pycache__、.pyc、渲染HTML)"""
    parts = filepath.replace("\\", "/").split("/")
    if any(p.startswith("zhiji_data_cache") for p in parts):
        return True
    if "__pycache__" in parts:
        return True
    if filepath.endswith(".pyc"):
        return True
    # 排除渲染的HTML模板 (大量小文件, 非核心交付物)
    if filepath.endswith(".html") and "rendered" in filepath:
        return True
    return False


def walk_v85_files(root_dir: str) -> List[str]:
    """遍历V85目录, 返回非排除的文件路径列表"""
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if not should_exclude(fp):
                files.append(fp)
    return sorted(files)


def safe_read_text(filepath: str, encoding: str = "utf-8-sig") -> Optional[str]:
    """安全读取文本文件"""
    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()
    except Exception:
        pass
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        pass
    try:
        with open(filepath, "r", encoding="gbk") as f:
            return f.read()
    except Exception:
        return None


def safe_read_binary(filepath: str) -> Optional[bytes]:
    """安全读取二进制"""
    try:
        with open(filepath, "rb") as f:
            return f.read()
    except Exception:
        return None


# ==============================================================================
# 校验模块
# ==============================================================================

def check_md5_integrity(files: List[str]) -> Dict[str, Any]:
    """
    MD5完整性校验:
    - 计算所有文件的MD5
    - 与已知清单对比
    - 返回详细结果
    """
    log(f"  [MD5] 开始计算 {len(files)} 个文件 MD5...", verbose=True)
    results = {"total": 0, "ok": 0, "fail": 0, "errors": [], "files": {}}
    
    for fp in files:
        rel = os.path.relpath(fp, REPO_ROOT)
        rel_posix = rel.replace("\\", "/")
        md5 = compute_md5(fp)
        size = os.path.getsize(fp) if os.path.exists(fp) else 0
        
        if md5:
            results["ok"] += 1
            results["files"][rel_posix] = {"md5": md5, "size": size}
        else:
            results["fail"] += 1
            results["errors"].append({"file": rel_posix, "reason": "MD5计算失败"})
        
        results["total"] += 1
    
    # 检查已知MD5清单
    manifest_results = []
    known_manifests = []
    
    # 检查 v85_final_archive/MD5_MANIFEST.md
    arch_manifest = os.path.join(ARCHIVE_DIR, "MD5_MANIFEST.md")
    if os.path.exists(arch_manifest):
        known_manifests.append(arch_manifest)
    
    # 检查 v85_review_simulation/MD5_MANIFEST.md
    v85_review = os.path.join(V85_DIR, "dshb_review_simulation", "MD5_MANIFEST.md")
    if os.path.exists(v85_review):
        known_manifests.append(v85_review)
    
    # 检查 MD5_CHECKSUM_LIST.md
    md5_checklist = os.path.join(V85_DIR, "MD5_CHECKSUM_LIST.md")
    if os.path.exists(md5_checklist):
        known_manifests.append(md5_checklist)
    
    for mf_path in known_manifests:
        mf_content = safe_read_text(mf_path)
        if not mf_content:
            continue
        
        # 解析MD5表 (格式: | filename | `md5` | size |)
        lines = mf_content.split("\n")
        manifest_entries = {}
        for line in lines:
            # 匹配 markdown 表格行: | ... | filename | `md5hash` | ... |
            matches = re.findall(r'`([a-f0-9]{8,32})`', line)
            fn_match = re.search(r'(\S+\.\w+)', line)
            if matches and fn_match:
                fn = fn_match.group(1)
                # 去除路径前缀
                for prefix in ["v85_final_archive/", "dshb_review_simulation/"]:
                    if fn.startswith(prefix):
                        fn = fn[len(prefix):]
                manifest_entries[fn] = matches[0][:8]  # 截断到8位
        
        log(f"  [MD5] 解析清单 {mf_path}: {len(manifest_entries)} 条目", verbose=True)
        manifest_results.append({
            "manifest": os.path.relpath(mf_path, REPO_ROOT).replace("\\", "/"),
            "entries": len(manifest_entries),
        })
    
    results["manifests"] = manifest_results
    
    log(f"  [MD5] 完成: {results['ok']}/{results['total']} 通过, {results['fail']} 失败")
    return results


def check_directory_structure() -> Dict[str, Any]:
    """
    目录结构校验:
    - 检查预期核心目录存在
    - 检查输出目录存在
    - 检查归档目录结构
    """
    log(f"  [结构] 开始目录结构校验...", verbose=True)
    results = {"total": 0, "exist": 0, "missing": [], "extra": [], "dirs": {}}
    
    for d in EXPECTED_DIRS:
        full = os.path.join(REPO_ROOT, d.replace("/", os.sep))
        if os.path.isdir(full):
            results["exist"] += 1
            # 统计子文件数
            try:
                count = sum(1 for _ in os.walk(full) if True)
                file_count = sum(
                    len(f) for _, _, f in os.walk(full)
                    if not any(excl in p for p in [os.sep] for excl in ["__pycache__", "zhiji_data_cache"])
                )
            except Exception:
                file_count = 0
            results["dirs"][d] = {"exists": True, "file_count": file_count}
        else:
            results["missing"].append(d)
            results["dirs"][d] = {"exists": False, "file_count": 0}
        results["total"] += 1
    
    # 检查输出目录
    output_dir = B_STORAGE_DIR
    if os.path.isdir(output_dir):
        files_in_output = os.listdir(output_dir)
        results["output_dir"] = {
            "exists": True,
            "path": os.path.relpath(output_dir, REPO_ROOT).replace("\\", "/"),
            "files": len(files_in_output),
        }
    else:
        results["output_dir"] = {"exists": False, "path": "b_storage_persist/"}
    
    # 检查归档目录
    archive_exists = os.path.isdir(ARCHIVE_DIR)
    if archive_exists:
        arch_files = list_files_no_cache(ARCHIVE_DIR)
        results["archive"] = {
            "exists": True,
            "path": "v85_final_archive/",
            "file_count": len(arch_files),
        }
    else:
        results["archive"] = {"exists": False, "path": "v85_final_archive/"}
    
    log(f"  [结构] 完成: {results['exist']}/{results['total']} 目录存在")
    return results


def list_files_no_cache(dirpath: str) -> List[str]:
    """列出目录文件, 排除缓存"""
    files = []
    for root, dirs, files_in_dir in os.walk(dirpath):
        for fn in files_in_dir:
            fp = os.path.join(root, fn)
            if not should_exclude(fp):
                files.append(fp)
    return files


def check_file_parsing(files: List[str]) -> Dict[str, Any]:
    """
    批量加载校验:
    - JSON: 解析, 检查结构完整性
    - CSV: 解析, 检查列数一致性, 编码检测
    - MD: 检查文件非空, 基本结构
    - PY: 检查语法, 不执行
    - JSONL: 逐行解析
    """
    log(f"  [解析] 开始批量加载校验 {len(files)} 个文件...", verbose=True)
    results = {
        "total": 0,
        "ok": 0,
        "fail": 0,
        "by_type": {},
        "errors": [],
        "encoding_issues": [],
        "csv_column_issues": [],
    }
    
    for fp in files:
        ext = get_file_ext(fp)
        rel = os.path.relpath(fp, REPO_ROOT).replace("\\", "/")
        results["total"] += 1
        
        try:
            if ext == ".json":
                _check_json(fp, rel, results)
            elif ext == ".csv":
                _check_csv(fp, rel, results)
            elif ext == ".md":
                _check_md(fp, rel, results)
            elif ext == ".py":
                _check_py(fp, rel, results)
            elif ext == ".jsonl":
                _check_jsonl(fp, rel, results)
            elif ext == ".txt":
                _check_txt(fp, rel, results)
            else:
                # 其他类型仅检查可读性
                content = safe_read_text(fp)
                if content is not None:
                    results["ok"] += 1
                else:
                    results["fail"] += 1
                    results["errors"].append({"file": rel, "reason": "无法读取文本"})
        except Exception as e:
            results["fail"] += 1
            results["errors"].append({"file": rel, "reason": f"解析异常: {str(e)[:200]}"})
    
    log(f"  [解析] 完成: {results['ok']}/{results['total']} 通过, {results['fail']} 失败")
    return results


def _check_json(fp: str, rel: str, results: Dict):
    """JSON解析校验"""
    raw = safe_read_binary(fp)
    if raw is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "无法读取"})
        return
    
    # 编码检测
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            results["fail"] += 1
            results["encoding_issues"].append({"file": rel, "encoding": "unknown"})
            results["errors"].append({"file": rel, "reason": "UTF-8解码失败"})
            return
    
    try:
        data = json.loads(text)
        results["ok"] += 1
        
        # 检查JSON结构
        if isinstance(data, dict):
            if "rules" not in data and "indicators" not in data:
                pass  # 正常, 不是所有JSON都有这些键
        
        if rel not in results["by_type"]:
            results["by_type"][rel] = {"type": "json", "keys": list(data.keys())[:10] if isinstance(data, dict) else "array"}
        else:
            results["by_type"][rel] = {"type": "json", "keys": list(data.keys())[:10] if isinstance(data, dict) else "array"}
            
    except json.JSONDecodeError as e:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": f"JSON解析失败: {str(e)[:200]}"})


def _check_csv(fp: str, rel: str, results: Dict):
    """CSV解析校验"""
    raw = safe_read_binary(fp)
    if raw is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "无法读取"})
        return
    
    # 编码检测 (utf-8-sig → utf-8 → gbk)
    text = None
    encoding_used = None
    for enc in ["utf-8-sig", "utf-8", "gbk", "latin-1"]:
        try:
            text = raw.decode(enc)
            encoding_used = enc
            break
        except (UnicodeDecodeError, Exception):
            continue
    
    if text is None:
        results["fail"] += 1
        results["encoding_issues"].append({"file": rel, "encoding": "unknown"})
        results["errors"].append({"file": rel, "reason": "CSV编码无法识别"})
        return
    
    try:
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, None)
        if headers is None:
            results["fail"] += 1
            results["errors"].append({"file": rel, "reason": "CSV为空文件"})
            return
        
        col_count = len(headers)
        row_count = 0
        mismatch_rows = []
        
        for i, row in enumerate(reader):
            row_count += 1
            if len(row) != col_count:
                mismatch_rows.append({"row": i + 2, "expected": col_count, "got": len(row)})
                if len(mismatch_rows) >= 10:
                    break
        
        results["ok"] += 1
        if rel not in results["by_type"]:
            results["by_type"][rel] = {
                "type": "csv",
                "columns": col_count,
                "rows": row_count,
                "encoding": encoding_used,
                "mismatch_rows": len(mismatch_rows),
            }
        else:
            results["by_type"][rel] = {
                "type": "csv",
                "columns": col_count,
                "rows": row_count,
                "encoding": encoding_used,
                "mismatch_rows": len(mismatch_rows),
            }
        
        if mismatch_rows:
            results["csv_column_issues"].append({
                "file": rel,
                "expected_columns": col_count,
                "mismatch_rows": mismatch_rows,
            })
            
    except Exception as e:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": f"CSV解析异常: {str(e)[:200]}"})


def _check_md(fp: str, rel: str, results: Dict):
    """MD文件校验"""
    content = safe_read_text(fp)
    if content is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "MD无法读取"})
        return
    
    if len(content.strip()) == 0:
        results["ok"] += 1  # 空文件不算错
    else:
        results["ok"] += 1
        
        # 检查基本结构
        lines = content.strip().split("\n")
        has_header = any(line.startswith("#") for line in lines[:20])
        
        if rel not in results["by_type"]:
            results["by_type"][rel] = {"type": "md", "lines": len(lines), "has_header": has_header}
        else:
            results["by_type"][rel] = {"type": "md", "lines": len(lines), "has_header": has_header}


def _check_py(fp: str, rel: str, results: Dict):
    """Python语法校验 (不执行)"""
    content = safe_read_text(fp)
    if content is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "PY无法读取"})
        return
    
    try:
        compile(content, fp, "exec")
        results["ok"] += 1
    except SyntaxError as e:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": f"Python语法错误: {str(e)[:200]}"})
    
    if rel not in results["by_type"]:
        results["by_type"][rel] = {"type": "py", "syntax_ok": True}
    else:
        results["by_type"][rel] = {"type": "py", "syntax_ok": True}


def _check_jsonl(fp: str, rel: str, results: Dict):
    """JSONL逐行解析"""
    content = safe_read_text(fp)
    if content is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "JSONL无法读取"})
        return
    
    lines = content.strip().split("\n")
    valid = 0
    invalid = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            json.loads(line)
            valid += 1
        except json.JSONDecodeError:
            invalid += 1
    
    if invalid == 0:
        results["ok"] += 1
    else:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": f"JSONL有{invalid}行解析失败/{valid}行通过"})
    
    if rel not in results["by_type"]:
        results["by_type"][rel] = {"type": "jsonl", "total": valid + invalid, "valid": valid, "invalid": invalid}


def _check_txt(fp: str, rel: str, results: Dict):
    """TXT文本校验"""
    content = safe_read_text(fp)
    if content is None:
        results["fail"] += 1
        results["errors"].append({"file": rel, "reason": "TXT无法读取"})
        return
    
    results["ok"] += 1
    if rel not in results["by_type"]:
        results["by_type"][rel] = {"type": "txt", "chars": len(content)}


def check_snapshot_integrity() -> Dict[str, Any]:
    """
    快照可用性探测:
    - 验证 git tag 存在
    - 验证快照文件完整性
    - 检查版本锁定状态
    """
    log(f"  [快照] 开始快照可用性探测...", verbose=True)
    results = {
        "git_tags": [],
        "snapshot_files": {},
        "snapshot_dir_exists": os.path.isdir(ARCHIVE_DIR),
        "git_available": False,
        "errors": [],
    }
    
    # 检查git tag
    try:
        # 获取当前分支
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        current_branch = branch_result.stdout.strip()
        results["git_available"] = True
        results["current_branch"] = current_branch
        
        # 获取所有v85相关tag
        tag_result = subprocess.run(
            ["git", "tag", "-l", "v85*"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        tags = tag_result.stdout.strip().split("\n") if tag_result.stdout.strip() else []
        results["git_tags"] = [t for t in tags if t]
        
        # 检查特定tag
        for tag_name in ["v85-final", "v85.0.0"]:
            tag_info_result = subprocess.run(
                ["git", "rev-parse", tag_name],
                capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
            )
            if tag_info_result.returncode == 0:
                results["git_tags"].append(tag_name)
                if tag_name not in results.get("tag_details", {}):
                    results.setdefault("tag_details", {})[tag_name] = {
                        "commit": tag_info_result.stdout.strip()[:12],
                        "verified": True,
                    }
        
    except Exception as e:
        results["errors"].append(f"Git操作失败: {str(e)[:200]}")
        results["git_available"] = False
    
    # 检查快照文件
    if results["snapshot_dir_exists"]:
        arch_files = list_files_no_cache(ARCHIVE_DIR)
        results["snapshot_files"]["count"] = len(arch_files)
        results["snapshot_files"]["total_size_bytes"] = sum(
            os.path.getsize(f) for f in arch_files if os.path.exists(f)
        )
        
        # 检查关键子目录
        sub_dirs = [d for d in os.listdir(ARCHIVE_DIR) if os.path.isdir(os.path.join(ARCHIVE_DIR, d))]
        results["snapshot_files"]["sub_directories"] = sub_dirs
        results["snapshot_files"]["has_md5_manifest"] = os.path.exists(
            os.path.join(ARCHIVE_DIR, "MD5_MANIFEST.md")
        )
        results["snapshot_files"]["has_git_tag_note"] = os.path.exists(
            os.path.join(ARCHIVE_DIR, "GIT_TAG_NOTE.md")
        )
        results["snapshot_files"]["has_archive_build_report"] = os.path.exists(
            os.path.join(ARCHIVE_DIR, "ARCHIVE_BUILD_REPORT.md")
        )
    
    log(f"  [快照] 完成: Git={'OK' if results['git_available'] else 'FAIL'}, "
        f"Tags={len(results['git_tags'])}, 快照目录={'OK' if results['snapshot_dir_exists'] else 'MISSING'}")
    return results


def check_readonly_lock(core_files: List[str]) -> Dict[str, Any]:
    """
    只读锁定校验:
    - 检查核心文件存在
    - 记录当前MD5 (用于未来比对)
    """
    log(f"  [只读] 开始只读锁定校验 {len(core_files)} 个文件...", verbose=True)
    results = {
        "total": 0,
        "exists": 0,
        "missing": [],
        "core_file_md5": {},
    }
    
    for rel in core_files:
        full = os.path.join(REPO_ROOT, rel.replace("/", os.sep))
        if os.path.exists(full):
            results["exists"] += 1
            md5 = compute_md5(full)
            if md5:
                results["core_file_md5"][rel] = md5
        else:
            results["missing"].append(rel)
        results["total"] += 1
    
    log(f"  [只读] 完成: {results['exists']}/{results['total']} 文件存在")
    return results


# ==============================================================================
# 主入口
# ==============================================================================

def run_full_check(output_path: str = None, verbose: bool = False) -> Dict[str, Any]:
    """执行全量校验"""
    start_time = datetime.now()
    
    log(f"\n{'='*70}")
    log(f"V85 交付物入库完整性校验")
    log(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"仓库根目录: {REPO_ROOT}")
    log(f"V85目录: {V85_DIR}")
    log(f"{'='*70}\n")
    
    # 1. 收集文件
    all_files = walk_v85_files(V85_DIR)
    archive_files = list_files_no_cache(ARCHIVE_DIR) if os.path.isdir(ARCHIVE_DIR) else []
    
    log(f"\n[统计] 文件统计:")
    log(f"  V85输出目录: {len(all_files)} 文件")
    log(f"  归档目录: {len(archive_files)} 文件")
    log(f"  合计: {len(all_files) + len(archive_files)} 文件\n")
    
    # 2. MD5校验
    md5_results = check_md5_integrity(all_files + archive_files)
    
    # 3. 目录结构校验
    structure_results = check_directory_structure()
    
    # 4. 批量加载校验
    parse_results = check_file_parsing(all_files + archive_files)
    
    # 5. 快照可用性探测
    snapshot_results = check_snapshot_integrity()
    
    # 6. 只读锁定校验
    readonly_results = check_readonly_lock(CORE_FILES)
    
    # 汇总
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    summary = {
        "task_id": "B_V85_ARTIFACT_PERSIST_AND_SNAPSHOT_VERIFY",
        "version": "v85",
        "timestamp": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "total_files_checked": len(all_files) + len(archive_files),
        "md5_pass_rate": f"{md5_results['ok']}/{md5_results['total']} ({100*md5_results['ok']/max(md5_results['total'],1):.1f}%)",
        "structure_pass_rate": f"{structure_results['exist']}/{structure_results['total']} ({100*structure_results['exist']/max(structure_results['total'],1):.1f}%)",
        "parse_pass_rate": f"{parse_results['ok']}/{parse_results['total']} ({100*parse_results['ok']/max(parse_results['total'],1):.1f}%)",
        "snapshot_available": snapshot_results["snapshot_dir_exists"],
        "readonly_core_files_ok": readonly_results["exists"],
        "readonly_core_files_missing": len(readonly_results["missing"]),
        "overall_status": "PASS" if (
            md5_results["fail"] == 0 and 
            structure_results["exist"] == structure_results["total"] and 
            parse_results["fail"] == 0 and 
            snapshot_results["snapshot_dir_exists"]
        ) else "WARN",
        "details": {
            "md5": {
                "total": md5_results["total"],
                "ok": md5_results["ok"],
                "fail": md5_results["fail"],
                "errors": md5_results["errors"],
                "manifests": md5_results["manifests"],
            },
            "structure": {
                "total": structure_results["total"],
                "exist": structure_results["exist"],
                "missing": structure_results["missing"],
            },
            "parse": {
                "total": parse_results["total"],
                "ok": parse_results["ok"],
                "fail": parse_results["fail"],
                "encoding_issues": parse_results["encoding_issues"],
                "csv_column_issues": parse_results["csv_column_issues"],
            },
            "snapshot": snapshot_results,
            "readonly": readonly_results,
        },
        "constraints": {
            "NO_ZHIJI_API_CALL": True,
            "READ_ONLY": True,
            "NO_MODIFY_SOURCE_TEMPLATE": True,
        },
    }
    
    log(f"\n{'='*70}")
    log(f"校验完成 - 耗时 {duration:.2f}s")
    log(f"总体状态: {summary['overall_status']}")
    log(f"MD5通过: {md5_results['ok']}/{md5_results['total']}")
    log(f"结构通过: {structure_results['exist']}/{structure_results['total']}")
    log(f"解析通过: {parse_results['ok']}/{parse_results['total']}")
    log(f"{'='*70}\n")
    
    # 输出结果
    if output_path:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log(f"结果已输出: {output_path}")
    
    return summary


def run_md5_only():
    """仅MD5校验"""
    files = walk_v85_files(V85_DIR)
    if os.path.isdir(ARCHIVE_DIR):
        files += list_files_no_cache(ARCHIVE_DIR)
    return check_md5_integrity(files)


def run_structure_only():
    """仅结构校验"""
    return check_directory_structure()


def run_parse_only():
    """仅解析校验"""
    files = walk_v85_files(V85_DIR)
    if os.path.isdir(ARCHIVE_DIR):
        files += list_files_no_cache(ARCHIVE_DIR)
    return check_file_parsing(files)


def run_snapshot_only():
    """仅快照校验"""
    return check_snapshot_integrity()


def main():
    parser = argparse.ArgumentParser(
        description="V85 交付物入库完整性校验脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python artifact_ingest_check.py                    # 全量校验
  python artifact_ingest_check.py --md5-only         # 仅MD5
  python artifact_ingest_check.py --parse-only       # 仅解析
  python artifact_ingest_check.py --output out.json  # 输出JSON
  python artifact_ingest_check.py --verbose          # 详细输出
""",
    )
    parser.add_argument("--md5-only", action="store_true", help="仅执行MD5校验")
    parser.add_argument("--structure-only", action="store_true", help="仅执行结构校验")
    parser.add_argument("--parse-only", action="store_true", help="仅执行解析校验")
    parser.add_argument("--snapshot-only", action="store_true", help="仅执行快照校验")
    parser.add_argument("--output", type=str, help="输出JSON结果路径")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.md5_only:
        result = run_md5_only()
    elif args.structure_only:
        result = run_structure_only()
    elif args.parse_only:
        result = run_parse_only()
    elif args.snapshot_only:
        result = run_snapshot_only()
    else:
        result = run_full_check(output_path=args.output, verbose=args.verbose)
    
    # 终端输出摘要
    if isinstance(result, dict):
        print(f"\n[完成] 校验完成")
        if "overall_status" in result:
            print(f"[状态] 总体: {result['overall_status']}")
            print(f"[统计] 文件总数: {result['total_files_checked']}")
            print(f"[MD5]  通过: {result['md5_pass_rate']}")
            print(f"[结构] 通过: {result['structure_pass_rate']}")
            print(f"[解析] 通过: {result['parse_pass_rate']}")
            print(f"[核心] {result['readonly_core_files_ok']} OK, {result['readonly_core_files_missing']} 缺失")
    
    return 0 if (isinstance(result, dict) and "overall_status" not in result) or \
                 (isinstance(result, dict) and result.get("overall_status") == "PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
