"""
v85_artifact_api.py
===================

V85 只读制品访问接口 —— 供评审门户读取 V85 冻结版本的分类数据（风险库、场景 A/B 回放、
别名冲突数据集、模板清单、Gate 结果、黑名单/别名库快照）。

设计原则
--------
1. **只读**：所有 GET 端点，禁止任何形式的写入。任何写入尝试都返回 403。
2. **不联网**：无 requests / httpx / urllib / socket 调用；不调用 zhiji API。
3. **不改业务结果**：只对外暴露 V85 冻结版本已有的产物文件；不在服务期内生成或改写数据。
4. **路径沙盒**：所有访问必须落在 ALLOWED_ROOTS 白名单内，且必须命中 ARTIFACTS 元数据表。
5. **版本可回溯**：版本号、tag、commit、产出目录、MD5、字节数均绑定到固定注册表。

对外依赖：Python 3.10+ 标准库。运行方式：
    from v85_artifact_api import ArtifactAPI
    api = ArtifactAPI(repo_root="D:/DSH_WORK/framework-tree")
    api.health()
    api.list_versions()
    api.get_artifact_meta("risk_db", version="f313570")
    api.verify_artifact_md5("alias_library", "1b7c4a2d3e5f6a78", version="f313570")
    api.query("risk_db", filters={"risk_level": "P0"}, limit=100)

命令行自检：
    python v85_artifact_api.py --smoke
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

__version__ = "1.0.0"
API_SCHEMA_VERSION = "v1"
TASK_ID = "E_V85_READONLY_API_AND_V86_BACKEND_DESIGN"

# --------------------------------------------------------------------------- #
# 1. 版本与制品注册表（V85 冻结基线）
# --------------------------------------------------------------------------- #

V85_VERSIONS: Dict[str, Dict[str, Any]] = {
    "f313570": {
        "version_tag": "v85.0",
        "commit_sha": "f3135709f1fd2c4ee8f972596ecde130e5128575",
        "commit_short": "f313570",
        "branch": "feature/v85-chart-template",
        "frozen_at": "2026-10-01T16:20:00+08:00",
        "output_root": "analysis/e2e_output/v85",
        "writable": False,
        "readable": True,
        "upstream": {
            "HERMES": "a2815c4",
            "DSHB": "6771406",
            "DSHE": "f313570",
        },
        "notes": "V85 最终冻结基线；DSHE 别名库审计与 V86 引擎设计已并入。",
    },
    # 保留字段：V86 未就绪时占位，避免评审门户出现 404
    "v86-dev": {
        "version_tag": "v86-dev-placeholder",
        "commit_sha": None,
        "commit_short": None,
        "branch": "feature/v86-alias-engine",
        "frozen_at": None,
        "output_root": "analysis/e2e_output/v86",
        "writable": False,
        "readable": False,
        "upstream": {},
        "notes": "占位：v86_init_backlog_total.md 未就绪前不提供读服务。",
    },
}

# 制品注册表：kind -> (relpath, 内容类型, 数据加载器)
# 所有 relpath 都是 analysis/e2e_output/v85 下的相对路径，绝不跨出该根。
ARTIFACTS: Dict[str, Dict[str, Any]] = {
    # --- 风险库 ---
    "risk_db": {
        "relpath": "unified_risk_db/unified_indicator_risk_db.csv",
        "schema_doc": "unified_risk_db/risk_db_schema.md",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "V85 统一指标风险数据库（PDF+THS 合并去重；含 P0/P1/P2 分级）",
        "keys": ["id", "risk_level", "template_id", "variety", "blacklist_id", "is_duplicate"],
        "filters": ["risk_level", "variety", "source", "blacklist_id", "risk_category", "conflict_type", "verify_status", "is_duplicate"],
    },
    "risk_db_schema": {
        "relpath": "unified_risk_db/risk_db_schema.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "风险库字段说明文档",
    },
    "risk_summary": {
        "relpath": "unified_risk_db/unified_risk_summary_report.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "风险汇总报告",
    },
    # --- 场景 A/B 回放 ---
    "scenario_replay": {
        "relpath": "dshb_full_integrate/full_488_template_playback_result.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "488 模板 PDF/THS 双场景回放结果",
        "keys": ["template_id", "source", "variety", "old_risk_label", "new_risk_label", "change_type", "is_cross_variety_p0"],
        "filters": ["source", "variety", "old_risk_label", "new_risk_label", "change_type", "is_cross_variety_p0", "verify_status"],
    },
    "chart_risk_bound": {
        "relpath": "v85_final_integrate/chart_risk_bound_all.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "图表-指标风险绑定全量文件（488 模板卡）",
    },
    "cross_variety_p0": {
        "relpath": "dshb_full_integrate/cross_variety_p0_validation.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "跨品种 P0 验证集",
        "keys": [],
        "filters": [],
    },
    # --- 别名库与冲突 ---
    "alias_library": {
        "relpath": "hermes_portal_gate_final/indicator_alias_library.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "别名库（最终评审交付版）",
        "keys": ["alias_id", "variety", "alias_type", "similarity_score", "source"],
        "filters": ["variety", "alias_type", "source"],
    },
    "alias_audit_sample": {
        "relpath": "dshe_alias_audit_design/alias_audit_sample.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "T2.1 分层抽样审计明细（120 行 × 49 列）",
        "keys": [],
        "filters": [],
    },
    "multi_canonical_conflicts": {
        "relpath": "dshe_alias_audit_design/multi_canonical_conflicts_165.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "165 条多规范冲突清单",
        "keys": ["alias_norm", "canonical_name", "confidence", "review_priority", "variety_family"],
        "filters": ["variety_family", "review_priority", "alias_type", "relation", "alias_source", "review_flag"],
    },
    "alias_conflict_classification": {
        "relpath": "dshe_alias_audit_design/multi_canonical_conflict_classification.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "多规范冲突分类结果",
        "keys": [],
        "filters": [],
    },
    "alias_test_case_set": {
        "relpath": "dshe_alias_audit_design/alias_test_case_set.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "V86 别名引擎回归测试集（893 用例）",
    },
    "ambiguous_indicator_list": {
        "relpath": "alias_lib_full_audit/ambiguous_indicator_list.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "歧义指标清单",
    },
    "high_risk_confusion_pairs": {
        "relpath": "hermes_portal_gate_final/high_risk_confusion_pairs.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "高风险混淆对",
    },
    # --- 模板清单 ---
    "template_manifest": {
        "relpath": "v85_final_integrate/ths_render_task_manifest.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "THS 渲染任务清单（155 模板）",
    },
    "template_task_list": {
        "relpath": "v85_final_integrate/ths_render_task_list.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "THS 渲染任务列表",
    },
    "template_task_summary": {
        "relpath": "v85_final_integrate/ths_render_task_summary.csv",
        "type": "csv",
        "content_type": "text/csv; charset=utf-8",
        "description": "THS 渲染任务汇总",
    },
    # --- 黑名单 / Gate ---
    "blacklist_v85_final": {
        "relpath": "dshb_full_integrate/semantic_blacklist_v85_final.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "V85 最终语义黑名单（31 条规则）",
    },
    "blacklist_v85_fixed": {
        "relpath": "unified_risk_db/semantic_blacklist_fixed.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "V85 修复版语义黑名单",
    },
    "blacklist_change_log": {
        "relpath": "dshb_full_integrate/blacklist_change_log.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "黑名单变更日志",
    },
    "gate_config": {
        "relpath": "dshe_alias_audit_design/regression_gate_config.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "回归 Gate 配置（14 项）",
    },
    "blacklist_rule_test": {
        "relpath": "dshe_alias_audit_design/blacklist_rule_test_result.json",
        "type": "json",
        "content_type": "application/json; charset=utf-8",
        "description": "黑名单规则效果测试（T2.6）",
    },
    # --- 设计文档 ---
    "v86_engine_design": {
        "relpath": "dshe_alias_audit_design/v86_alias_engine_full_design.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V86 别名引擎完整设计",
    },
    "v86_gate_fusion": {
        "relpath": "dshe_alias_audit_design/v86_gate_fusion_framework.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V86 Gate 融合框架",
    },
    "v85_delivery_manifest": {
        "relpath": "hermes_v85_final_delivery/v85_full_delivery_manifest_v2.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V85 完整交付清单 v2",
    },
    "v85_delivery_readme": {
        "relpath": "hermes_v85_final_delivery/v85_delivery_readme.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V85 交付顶层 README",
    },
    "v85_gate_acceptance": {
        "relpath": "hermes_v85_final_delivery/v85_gate_final_acceptance_report.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "Gate 最终验收报告",
    },
    "portal_v6_final": {
        "relpath": "hermes_v85_final_delivery/enhanced_review_portal_v6_final.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V6 验收门户",
    },
    "dshb_gate_summary": {
        "relpath": "dshb_final_gate_summary/dsh_final_gate_acceptance.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "DSHB 最终 Gate 验收（10 项三态判定）",
    },
    "dshb_rule_summary": {
        "relpath": "dshb_final_gate_summary/v85_rule_full_summary.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V85 全套风险规则总览（31 规则 + 1 候选）",
    },
    "dshb_v86_milestone": {
        "relpath": "dshb_final_gate_summary/v86_rule_milestone_ticket.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V86 规则迭代细化工单",
    },
    # --- 本任务交付 ---
    "e_api_spec": {
        "relpath": "e_api_design/api_spec_v85_readonly.md",
        "type": "markdown",
        "content_type": "text/markdown; charset=utf-8",
        "description": "V85 只读接口文档",
    },
}

# 允许的写入目标（当前为空：只读）
WRITE_TARGETS: Tuple[str, ...] = ()

# 认证：Bearer Token -> (username, roles, expires_at)
# 生产应替换为 JWT + 白名单；此处仅为接口骨架示范。
TOKENS: Dict[str, Dict[str, Any]] = {
    "v85-portal-r-0001": {"user": "portal_ro", "roles": {"portal_read"}, "expires_at": "2026-12-31T23:59:59+08:00"},
    "v85-reviewer-r-0001": {"user": "reviewer_ro", "roles": {"portal_read", "audit_read"}, "expires_at": "2026-12-31T23:59:59+08:00"},
    "v85-admin-readonly-0001": {"user": "admin_ro", "roles": {"portal_read", "audit_read", "ops_read"}, "expires_at": "2026-12-31T23:59:59+08:00"},
    # 写入令牌示例（永不被接受；用于验证写保护）
    "v85-portal-w-0001": {"user": "portal_wo", "roles": {"portal_write"}, "expires_at": "2026-12-31T23:59:59+08:00"},
}

ROLE_ACTIONS: Dict[str, Tuple[str, ...]] = {
    "portal_read": ("list_versions", "get_artifact_meta", "query", "download", "verify_md5", "get_file", "health"),
    "audit_read": ("list_versions", "get_artifact_meta", "query", "download", "verify_md5", "get_file", "health", "list_audit"),
    "ops_read": ("health", "metrics"),
    "portal_write": (),  # 显式禁止：任何写入动作
}

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE", "TRACE", "CONNECT", "OPTIONS"}

# 速率限制（简化：全局计数器）
RATE_LIMIT_PER_MINUTE = 300
_requests: List[float] = []

MAX_LIMIT_DEFAULT = 100
MAX_LIMIT_HARD = 10000
MAX_DEPTH = 8
MAX_FILTER_OPS = 24
MAX_PAGE_SIZE = 1000


# --------------------------------------------------------------------------- #
# 2. 错误类型
# --------------------------------------------------------------------------- #

def _resolve_default_repo_root() -> str:
    """SMK-01 修复：仓库根解析，消除硬编码路径。

    优先级：
      1. 环境变量 FRAMEWORK_TREE（部署注入）
      2. 本文件所在仓库根（Path(__file__).parents[4]，
         file: <repo>/analysis/e2e_output/v85/e_api_design/v85_artifact_api.py）
    原实现硬编码 Windows 路径 D:/DSH_WORK/framework-tree，Linux 部署必崩。
    """
    env = os.environ.get("FRAMEWORK_TREE")
    if env:
        return env
    return str(Path(__file__).resolve().parents[4])


HARDCODED_REPO_ROOT_DEPRECATED: str = "D:/DSH_WORK/framework-tree"


class ApiError(Exception):
    status = 500

    def __init__(self, code: str, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime()),
        }


class UnauthorizedError(ApiError):
    status = 401


class ForbiddenError(ApiError):
    status = 403


class NotFoundError(ApiError):
    status = 404


class BadRequestError(ApiError):
    status = 400


class MethodNotAllowedError(ApiError):
    status = 405


class RateLimitedError(ApiError):
    status = 429


class Md5MismatchError(ApiError):
    status = 422


class WriteForbiddenError(ApiError):
    status = 403


# --------------------------------------------------------------------------- #
# 3. 版本解析
# --------------------------------------------------------------------------- #

_VERSION_RE = re.compile(r"^[0-9a-fA-F]{7,40}$|^(v?\d+\.\d+(-[a-z]+)?)$|^v86-dev$")


def resolve_version(version: Optional[str] = None) -> Dict[str, Any]:
    """解析版本号/commit hash/tag。默认 f313570。"""
    if version is None or version == "":
        return dict(V85_VERSIONS["f313570"])

    # 1) 直接命中注册表 key
    if version in V85_VERSIONS:
        v = dict(V85_VERSIONS[version])
    else:
        # 2) 遍历注册表，匹配 commit_sha / commit_short / version_tag / branch
        hit = None
        for _, v in V85_VERSIONS.items():
            if (
                v.get("commit_sha") == version
                or v.get("commit_short") == version
                or v.get("version_tag") == version
                or v.get("branch") == version
            ):
                hit = v
                break
        if hit is None:
            raise NotFoundError(
                "VERSION_NOT_FOUND",
                f"版本 '{version}' 未在注册表中登记",
                {"registered_versions": list(V85_VERSIONS.keys())},
            )
        v = dict(hit)

    if not v.get("readable", False):
        raise ForbiddenError(
            "VERSION_READ_FORBIDDEN",
            f"版本 '{version}' 未开放读服务",
            {"version": version, "readable": v.get("readable")},
        )
    if v.get("writable", True):
        raise ForbiddenError(
            "VERSION_WRITABLE",
            f"版本 '{version}' 不允许写入",
            {"version": version},
        )
    return v


# --------------------------------------------------------------------------- #
# 4. API 主类
# --------------------------------------------------------------------------- #

class ArtifactAPI:
    """V85 只读制品访问接口（进程内调用）。

    每个方法对应 REST API 的一个端点，返回 dict（等价于 HTTP JSON 响应体）。
    失败时抛 ApiError 子类；上层 REST 适配层可以捕获并转 HTTP 状态码。
    """

    def __init__(
        self,
        repo_root: Optional[str] = None,
        token: Optional[str] = None,
        rate_limiter: Optional[bool] = True,
    ) -> None:
        # SMK-01 修复：默认 repo_root 由 _resolve_default_repo_root() 决定
        actual_root = repo_root or _resolve_default_repo_root()
        self.repo_root = Path(actual_root)
        self.output_root = self.repo_root / "analysis" / "e2e_output" / "v85"
        self.token = token
        self.rate_limiter = rate_limiter
        self._md5_cache: Dict[str, Tuple[str, int]] = {}  # relpath -> (md5, size)

        if not self.output_root.exists():
            raise RuntimeError(
                f"V85 输出根目录不存在: {self.output_root}。"
                "请确认 repo_root 指向 framework-tree 仓库。"
            )

    # ------------------------------------------------------------------ #
    # 认证 / 鉴权
    # ------------------------------------------------------------------ #

    def _auth(self, required_role: str) -> Dict[str, Any]:
        if not self.token:
            raise UnauthorizedError("NO_TOKEN", "缺少 Authorization: Bearer <token>")
        entry = TOKENS.get(self.token)
        if entry is None:
            raise UnauthorizedError("BAD_TOKEN", f"未识别的令牌 {self.token[:8]}...")
        if required_role not in entry["roles"]:
            raise ForbiddenError(
                "ROLE_FORBIDDEN",
                f"角色 '{required_role}' 不在令牌权限集 {sorted(entry['roles'])}",
                {"token_prefix": self.token[:8], "required": required_role},
            )
        return entry

    def _rate_check(self) -> None:
        if not self.rate_limiter:
            return
        now = time.time()
        # 保留最近 60 秒的请求
        _requests[:] = [t for t in _requests if now - t < 60]
        _requests.append(now)
        if len(_requests) > RATE_LIMIT_PER_MINUTE:
            raise RateLimitedError("RATE_LIMIT", f"每分钟超过 {RATE_LIMIT_PER_MINUTE} 次调用")

    def _resolve_file(self, kind: str, version: Optional[str] = None) -> Path:
        """根据制品 kind 解析绝对路径，并做白名单/存在性校验。"""
        meta = ARTIFACTS.get(kind)
        if meta is None:
            raise NotFoundError("ARTIFACT_NOT_REGISTERED", f"制品 '{kind}' 未在 ARTIFACTS 中登记",
                               {"registered": sorted(ARTIFACTS.keys())})
        v = resolve_version(version)
        rel = meta["relpath"]
        path = (self.output_root / rel).resolve()
        # 沙盒检查：必须严格在 output_root 之下
        try:
            path.relative_to(self.output_root.resolve())
        except ValueError:
            raise ForbiddenError("PATH_ESCAPE", f"制品路径越出白名单根: {rel}")
        if not path.exists():
            raise NotFoundError("ARTIFACT_FILE_MISSING", f"制品文件缺失: {rel}",
                                {"kind": kind, "version_tag": v["version_tag"]})
        return path

    # ------------------------------------------------------------------ #
    # 只读端点
    # ------------------------------------------------------------------ #

    def health(self) -> Dict[str, Any]:
        self._rate_check()
        return {
            "status": "ok",
            "api_schema": API_SCHEMA_VERSION,
            "module": __name__,
            "version": __version__,
            "task_id": TASK_ID,
            "read_only": True,
            "no_zhiji_api_call": True,
            "uptime_seconds": 0,
            "registered_versions": len(V85_VERSIONS),
            "registered_artifacts": len(ARTIFACTS),
        }

    def list_versions(self, include_inactive: bool = False) -> Dict[str, Any]:
        self._auth("portal_read")
        self._rate_check()
        versions = []
        for key, v in V85_VERSIONS.items():
            entry = {"key": key, **v}
            if not include_inactive and not entry.get("readable", False):
                continue
            versions.append(entry)
        return {"versions": versions, "count": len(versions), "read_only": True}

    def list_artifacts(self, version: Optional[str] = None) -> Dict[str, Any]:
        self._auth("portal_read")
        self._rate_check()
        v = resolve_version(version)
        items = []
        for kind, meta in ARTIFACTS.items():
            path = self.output_root / meta["relpath"]
            exists = path.exists()
            items.append({
                "kind": kind,
                "relpath": meta["relpath"],
                "content_type": meta.get("content_type"),
                "description": meta.get("description"),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
            })
        return {
            "version": v["version_tag"],
            "commit_sha": v["commit_sha"],
            "artifacts": items,
            "count": len(items),
            "read_only": True,
        }

    def get_artifact_meta(self, kind: str, version: Optional[str] = None) -> Dict[str, Any]:
        self._auth("portal_read")
        self._rate_check()
        v = resolve_version(version)
        meta = ARTIFACTS.get(kind)
        if meta is None:
            raise NotFoundError("ARTIFACT_NOT_REGISTERED", f"制品 '{kind}' 未登记")
        path = self.output_root / meta["relpath"]
        exists = path.exists()
        out = {
            "kind": kind,
            "relpath": meta["relpath"],
            "content_type": meta.get("content_type"),
            "type": meta.get("type"),
            "description": meta.get("description"),
            "keys": meta.get("keys", []),
            "filters": meta.get("filters", []),
            "version": v["version_tag"],
            "commit_sha": v["commit_sha"],
            "exists": exists,
        }
        if exists:
            md5, size = self._md5_of(path)
            out.update({
                "size_bytes": size,
                "md5": md5,
                "last_modified": time.strftime(
                    "%Y-%m-%dT%H:%M:%S+08:00", time.localtime(path.stat().st_mtime)),
            })
        return out

    def verify_artifact_md5(
        self,
        kind: str,
        expected_md5: str,
        version: Optional[str] = None,
        verify_file: bool = False,
    ) -> Dict[str, Any]:
        """校验制品 MD5。verify_file=True 时用实时读盘计算，否则用缓存。"""
        self._auth("portal_read")
        self._rate_check()
        v = resolve_version(version)
        kind_meta = ARTIFACTS.get(kind)
        if kind_meta is None:
            raise NotFoundError("ARTIFACT_NOT_REGISTERED", f"制品 '{kind}' 未登记")
        path = self.output_root / kind_meta["relpath"]
        if not path.exists():
            raise NotFoundError("ARTIFACT_FILE_MISSING", f"制品文件缺失: {kind_meta['relpath']}")

        expected = expected_md5.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{32}", expected):
            raise BadRequestError("BAD_MD5_FORMAT", f"期望 MD5 应为 32 位十六进制，收到: {expected_md5!r}")

        if verify_file:
            actual = self._md5_bytes(path.read_bytes()).lower()
            cache = False
        else:
            actual, _ = self._md5_of(path)
            cache = True

        ok = (actual == expected)
        if not ok and verify_file:
            # 实时校验失败直接返回 422 而不抛异常
            return {
                "kind": kind,
                "version": v["version_tag"],
                "expected_md5": expected,
                "actual_md5": actual,
                "match": False,
                "verified_from_cache": cache,
                "note": "MD5 不匹配：本地文件与期望值不一致；可能是版本错配或文件被替换。",
            }
        return {
            "kind": kind,
            "version": v["version_tag"],
            "expected_md5": expected,
            "actual_md5": actual,
            "match": ok,
            "verified_from_cache": cache,
            "commit_sha": v["commit_sha"],
        }

    def get_file(self, kind: str, version: Optional[str] = None) -> Dict[str, Any]:
        """小文件直接返回内容（<= 256 KiB），大文件只返回元数据 + sha256。"""
        self._auth("portal_read")
        self._rate_check()
        v = resolve_version(version)
        path = self._resolve_file(kind, version)
        size = path.stat().st_size
        meta = ARTIFACTS[kind]

        if size > 256 * 1024:
            md5, _ = self._md5_of(path)
            return {
                "kind": kind,
                "relpath": meta["relpath"],
                "version": v["version_tag"],
                "size_bytes": size,
                "md5": md5,
                "content_type": meta.get("content_type"),
                "content": None,
                "content_note": "文件 > 256 KiB，仅提供元数据；请调用 query() 端点分页读取。",
                "read_only": True,
            }

        raw = path.read_bytes()
        md5 = self._md5_bytes(raw).lower()
        if meta.get("type") in {"csv", "markdown"}:
            text = raw.decode("utf-8", errors="replace")
            return {
                "kind": kind,
                "relpath": meta["relpath"],
                "version": v["version_tag"],
                "size_bytes": size,
                "md5": md5,
                "content_type": meta.get("content_type"),
                "content": text,
                "encoding": "utf-8",
                "read_only": True,
            }
        if meta.get("type") == "json":
            return {
                "kind": kind,
                "relpath": meta["relpath"],
                "version": v["version_tag"],
                "size_bytes": size,
                "md5": md5,
                "content_type": meta.get("content_type"),
                "content": json.loads(raw.decode("utf-8", errors="replace")),
                "encoding": "utf-8",
                "read_only": True,
            }
        # 其他类型走 base64
        return {
            "kind": kind,
            "relpath": meta["relpath"],
            "version": v["version_tag"],
            "size_bytes": size,
            "md5": md5,
            "content_type": meta.get("content_type") or "application/octet-stream",
            "content_b64": base64.b64encode(raw).decode("ascii"),
            "read_only": True,
        }

    def query(
        self,
        kind: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = MAX_LIMIT_DEFAULT,
        offset: int = 0,
        sort: Optional[str] = None,
        reverse: bool = False,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页查询。filters 只允许 {field: scalar_value} 或 {field: {"op": "...", "value": ...}}。

        支持的 op: eq / ne / in / contains / lt / le / gt / ge / regex
        """
        self._auth("portal_read")
        self._rate_check()
        v = resolve_version(version)
        meta = ARTIFACTS.get(kind)
        if meta is None:
            raise NotFoundError("ARTIFACT_NOT_REGISTERED", f"制品 '{kind}' 未登记")
        if meta.get("type") not in {"csv", "json"}:
            raise BadRequestError("QUERY_NOT_SUPPORTED", f"制品 '{kind}' 不支持 query()，只有 csv/json 支持")

        limit = int(limit)
        offset = int(offset)
        if not (1 <= limit <= MAX_LIMIT_HARD):
            raise BadRequestError("BAD_LIMIT", f"limit 必须在 [1, {MAX_LIMIT_HARD}]，收到 {limit}")
        if offset < 0:
            raise BadRequestError("BAD_OFFSET", f"offset 必须 >= 0，收到 {offset}")
        if sort is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sort):
            raise BadRequestError("BAD_SORT", f"sort 字段名非法: {sort!r}")

        filters = filters or {}
        if len(filters) > MAX_FILTER_OPS:
            raise BadRequestError("FILTERS_TOO_MANY", f"过滤字段超过 {MAX_FILTER_OPS}")

        path = self._resolve_file(kind, version)
        if meta["type"] == "csv":
            rows = self._load_csv(path)
        else:  # json
            rows = self._load_json_list(path)

        total = len(rows)
        filtered = self._apply_filters(rows, filters, allowed_keys=set(meta.get("filters") or []))
        if sort is not None:
            try:
                filtered = sorted(filtered, key=lambda r: (str(r.get(sort, "")),), reverse=reverse)
            except Exception as exc:
                raise BadRequestError("BAD_SORT_KEY", f"排序字段不可比较: {exc}")
        page = filtered[offset:offset + limit]
        return {
            "kind": kind,
            "version": v["version_tag"],
            "commit_sha": v["commit_sha"],
            "total": total,
            "filtered": len(filtered),
            "offset": offset,
            "limit": limit,
            "returned": len(page),
            "next_offset": offset + limit if offset + limit < len(filtered) else None,
            "filters": filters,
            "sort": {"field": sort, "reverse": reverse} if sort else None,
            "rows": page,
            "read_only": True,
        }

    def list_audit(self, version: Optional[str] = None) -> Dict[str, Any]:
        """列出本目录已生成/被登记的所有产物（含 e_api_design 自身）。"""
        self._auth("audit_read")
        self._rate_check()
        v = resolve_version(version)
        rows: List[Dict[str, Any]] = []
        for kind, meta in ARTIFACTS.items():
            path = self.output_root / meta["relpath"]
            exists = path.exists()
            md5 = self._md5_of(path)[0] if exists else None
            size = path.stat().st_size if exists else None
            rows.append({
                "kind": kind,
                "relpath": meta["relpath"],
                "exists": exists,
                "size_bytes": size,
                "md5": md5,
            })
        return {
            "version": v["version_tag"],
            "commit_sha": v["commit_sha"],
            "rows": rows,
            "count": len(rows),
            "read_only": True,
        }

    def metrics(self) -> Dict[str, Any]:
        self._auth("ops_read")
        self._rate_check()
        return {
            "api_version": __version__,
            "api_schema": API_SCHEMA_VERSION,
            "registered_artifacts": len(ARTIFACTS),
            "registered_versions": len(V85_VERSIONS),
            "read_only": True,
            "no_zhiji_api_call": True,
            "requests_last_60s": len([t for t in _requests if time.time() - t < 60]),
            "cache_hits": len(self._md5_cache),
        }

    # ------------------------------------------------------------------ #
    # 写端点（全部显式拒绝）
    # ------------------------------------------------------------------ #

    def _reject_write(self, method: str, path: str, body: Any = None) -> Dict[str, Any]:
        """统一写保护拦截。任何 method 属于 WRITE_METHODS 一律 403。"""
        raise WriteForbiddenError(
            "WRITE_FORBIDDEN",
            f"V85 冻结版本拒绝 {method} {path}；仅允许只读访问。",
            {
                "method": method,
                "path": path,
                "body_bytes": len(str(body)) if body is not None else 0,
                "policy": "V85 frozen; write operations are not permitted.",
                "alternatives": [
                    "调用 GET /api/v1/versions 查询版本",
                    "调用 GET /api/v1/artifacts/{kind} 查询制品",
                    "调用 GET /api/v1/artifacts/{kind}/query 分页读取",
                ],
            },
        )

    # 显式写入口：便于路由层统一调用
    def put(self, path: str, body: Any = None) -> Dict[str, Any]:
        return self._reject_write("PUT", path, body)

    def post(self, path: str, body: Any = None) -> Dict[str, Any]:
        return self._reject_write("POST", path, body)

    def patch(self, path: str, body: Any = None) -> Dict[str, Any]:
        return self._reject_write("PATCH", path, body)

    def delete(self, path: str, body: Any = None) -> Dict[str, Any]:
        return self._reject_write("DELETE", path, body)

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    @staticmethod
    def _md5_bytes(raw: bytes) -> str:
        return hashlib.md5(raw).hexdigest()

    def _md5_of(self, path: Path) -> Tuple[str, int]:
        key = str(path)
        cached = self._md5_cache.get(key)
        if cached is not None:
            return cached
        size = path.stat().st_size
        # 流式分块
        h = hashlib.md5()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        md5 = h.hexdigest()
        self._md5_cache[key] = (md5, size)
        return md5, size

    def _load_csv(self, path: Path) -> List[Dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            return [dict(r) for r in reader]

    def _load_json_list(self, path: Path) -> List[Dict[str, Any]]:
        raw = path.read_text(encoding="utf-8")
        obj = json.loads(raw)
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict):
            # 常见包装： {"rules": [...]} / {"cases": [...]} / {"templates": [...]} / {"templates": {...}}
            for key in ("rules", "cases", "templates", "items", "data", "records", "test_cases"):
                v = obj.get(key)
                if isinstance(v, list):
                    return v
                if isinstance(v, dict) and all(isinstance(x, (str, int, float)) for x in v):
                    # 视为 key-value 表
                    return [{"_key": k, "_value": v[k]} for k in v]
            # 否则返回单元素包装
            return [obj]
        return []

    @staticmethod
    def _apply_filters(
        rows: List[Dict[str, Any]],
        filters: Dict[str, Any],
        allowed_keys: Sequence[str] = (),
    ) -> List[Dict[str, Any]]:
        allowed = set(allowed_keys)
        ops_by_field: List[Tuple[str, Any]] = []
        for field, spec in filters.items():
            if allowed and field not in allowed:
                raise BadRequestError(
                    "FILTER_NOT_ALLOWED",
                    f"字段 '{field}' 不在过滤白名单 {sorted(allowed)}",
                )
            if isinstance(spec, dict) and "op" in spec:
                ops_by_field.append((field, (spec["op"], spec.get("value"))))
            else:
                ops_by_field.append((field, ("eq", spec)))

        out: List[Dict[str, Any]] = []
        for row in rows:
            ok = True
            for field, (op, value) in ops_by_field:
                rv = row.get(field)
                ok = _filter_match(rv, op, value)
                if not ok:
                    break
            if ok:
                out.append(row)
        return out


def _filter_match(row_value: Any, op: str, value: Any) -> bool:
    """按 op 判定 row_value 是否匹配 value。"""
    if op == "eq":
        return str(row_value) == str(value)
    if op == "ne":
        return str(row_value) != str(value)
    if op == "in":
        return str(row_value) in {str(x) for x in value} if isinstance(value, (list, tuple, set)) else False
    if op == "contains":
        return str(value) in str(row_value)
    if op == "regex":
        try:
            return re.search(str(value), str(row_value)) is not None
        except re.error:
            return False
    if op in {"lt", "le", "gt", "ge"}:
        try:
            a, b = float(row_value), float(value)
        except (TypeError, ValueError):
            return False
        if op == "lt":
            return a < b
        if op == "le":
            return a <= b
        if op == "gt":
            return a > b
        return a >= b
    raise BadRequestError("BAD_OP", f"不支持的过滤 op: {op}")


# --------------------------------------------------------------------------- #
# 5. 简易路由适配（供未来 Web 层复用；本文件不启动 HTTP 服务）
# --------------------------------------------------------------------------- #

def dispatch(api: ArtifactAPI, method: str, path: str, query: Optional[Dict[str, Any]] = None,
             body: Any = None) -> Dict[str, Any]:
    """把 REST 请求路由到 ArtifactAPI 方法。返回 JSON 兼容 dict。

    路由表：
      GET  /api/v1/health
      GET  /api/v1/versions
      GET  /api/v1/artifacts
      GET  /api/v1/artifacts/{kind}
      GET  /api/v1/artifacts/{kind}/query
      GET  /api/v1/artifacts/{kind}/file
      GET  /api/v1/artifacts/{kind}/verify
      GET  /api/v1/audit
      GET  /api/v1/metrics
    """
    method = method.upper()
    if method in WRITE_METHODS:
        api._reject_write(method, path, body)

    if method != "GET":
        raise MethodNotAllowedError("METHOD_NOT_ALLOWED", f"仅支持 GET，收到 {method}")

    query = dict(query or {})
    version = query.pop("version", None)

    def _kind_match(pattern: str) -> Optional[str]:
        parts = [p for p in pattern.split("/") if p]
        qparts = [p for p in path.split("/") if p]
        if len(parts) != len(qparts):
            return None
        for a, b in zip(parts, qparts):
            if a.startswith("{") and a.endswith("}"):
                continue
            if a != b:
                return None
        for a, b in zip(parts, qparts):
            if a.startswith("{") and a.endswith("}"):
                return b
        return None

    routes = [
        ("GET", "/api/v1/health", lambda: api.health()),
        ("GET", "/api/v1/versions", lambda: api.list_versions(include_inactive=query.get("include_inactive") in {"1", "true", True})),
        ("GET", "/api/v1/artifacts", lambda: api.list_artifacts(version=version)),
        ("GET", "/api/v1/artifacts/{kind}", lambda: api.get_artifact_meta(kind, version=version)),
        ("GET", "/api/v1/artifacts/{kind}/query", None),  # 需 query 参数
        ("GET", "/api/v1/artifacts/{kind}/file", lambda: api.get_file(kind, version=version)),
        ("GET", "/api/v1/artifacts/{kind}/verify", None),
        ("GET", "/api/v1/audit", lambda: api.list_audit(version=version)),
        ("GET", "/api/v1/metrics", lambda: api.metrics()),
    ]
    for m, pattern, handler in routes:
        kind = _kind_match(pattern) if "{" in pattern else None
        matches = (kind is not None) if "{" in pattern else (path == pattern)
        if not matches:
            continue
        if pattern.endswith("/query"):
            return api.query(
                kind,
                filters=query.get("filters") or {},
                limit=int(query.get("limit", MAX_LIMIT_DEFAULT)),
                offset=int(query.get("offset", 0)),
                sort=query.get("sort"),
                reverse=query.get("reverse") in {"1", "true", True},
                version=version,
            )
        if pattern.endswith("/verify"):
            expected = query.get("expected_md5") or query.get("expected")
            if not expected:
                raise BadRequestError("MISSING_MD5", "verify 端点必须提供 expected_md5")
            return api.verify_artifact_md5(
                kind, expected, version=version,
                verify_file=query.get("verify_file") in {"1", "true", True},
            )
        return handler()

    raise NotFoundError("ROUTE_NOT_FOUND", f"无匹配路由: {method} {path}")


# --------------------------------------------------------------------------- #
# 6. 命令行自检
# --------------------------------------------------------------------------- #

def _smoke(repo_root: str) -> int:
    """跑一遍冒烟测试：健康/版本/元数据/MD5 校验/查询/写保护。"""
    api = ArtifactAPI(repo_root=repo_root, token="v85-portal-r-0001")
    failures: List[str] = []

    def _check(name: str, cond: bool, msg: str = "") -> None:
        if not cond:
            failures.append(f"{name}: {msg}")

    try:
        h = api.health()
        _check("health", h["status"] == "ok" and h["read_only"] is True)
    except Exception as exc:
        failures.append(f"health raised {exc}")

    try:
        vs = api.list_versions()
        _check("versions", vs["count"] >= 1 and vs["read_only"] is True)
    except Exception as exc:
        failures.append(f"versions raised {exc}")

    try:
        meta = api.get_artifact_meta("risk_db")
        _check("meta risk_db", meta["exists"] and meta["md5"] and meta["size_bytes"] > 0)
    except Exception as exc:
        failures.append(f"meta raised {exc}")

    try:
        v = api.verify_artifact_md5("risk_db", meta["md5"])
        _check("md5 verify", v["match"] is True)
    except Exception as exc:
        failures.append(f"md5 verify raised {exc}")

    try:
        v_bad = api.verify_artifact_md5("risk_db", "00000000000000000000000000000000", verify_file=True)
        _check("md5 mismatch", v_bad["match"] is False)
    except Exception as exc:
        failures.append(f"md5 mismatch raised {exc}")

    try:
        q = api.query("risk_db", filters={"risk_level": "P0"}, limit=5)
        _check("query P0", q["returned"] == 5 and all(r.get("risk_level") == "P0" for r in q["rows"]))
    except Exception as exc:
        failures.append(f"query raised {exc}")

    try:
        q2 = api.query("risk_db", filters={"risk_level": {"op": "in", "value": ["P0", "P1"]}}, limit=10, sort="template_id")
        _check("query in", q2["returned"] <= 10)
    except Exception as exc:
        failures.append(f"query in raised {exc}")

    # 未登记制品
    try:
        api.get_artifact_meta("__nope__")
        failures.append("get_artifact_meta should raise")
    except NotFoundError:
        pass

    # 写保护
    for method_name in ("put", "post", "patch", "delete"):
        try:
            getattr(api, method_name)("/api/v1/artifacts/risk_db", {"hack": True})
            failures.append(f"{method_name} should raise")
        except WriteForbiddenError:
            pass

    # 无 token
    api_no = ArtifactAPI(repo_root=repo_root, token=None)
    try:
        api_no.list_versions()
        failures.append("list_versions no-token should raise")
    except UnauthorizedError:
        pass

    # 无权限角色
    api_write = ArtifactAPI(repo_root=repo_root, token="v85-portal-w-0001")
    try:
        api_write.list_versions()
        failures.append("list_versions write-token should be forbidden")
    except ForbiddenError:
        pass

    # 路由分发
    try:
        r = dispatch(api, "GET", "/api/v1/artifacts/risk_db/query", {"limit": 3})
        _check("dispatch query", r["returned"] == 3)
    except Exception as exc:
        failures.append(f"dispatch raised {exc}")

    # 路由写保护
    try:
        dispatch(api, "POST", "/api/v1/artifacts/risk_db", {"x": 1})
        failures.append("dispatch POST should raise")
    except WriteForbiddenError:
        pass

    print(json.dumps({
        "smoke": "PASS" if not failures else "FAIL",
        "repo_root": repo_root,
        "artifacts": len(ARTIFACTS),
        "versions": list(V85_VERSIONS.keys()),
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def _main() -> int:
    parser = argparse.ArgumentParser(description="V85 Read-Only Artifact API")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--list-artifacts", action="store_true", help="List registered artifacts")
    parser.add_argument("--meta", help="Print artifact meta for given kind")
    args = parser.parse_args()

    if args.smoke:
        # SMK-01 修复：未显式传参时走自动解析
        rr = args.repo_root or _resolve_default_repo_root()
        return _smoke(rr)

    api = ArtifactAPI(repo_root=args.repo_root, token="v85-portal-r-0001")
    if args.list_artifacts:
        print(json.dumps(api.list_artifacts(), ensure_ascii=False, indent=2))
        return 0
    if args.meta:
        print(json.dumps(api.get_artifact_meta(args.meta), ensure_ascii=False, indent=2))
        return 0
    print("Use --smoke / --list-artifacts / --meta <kind>")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
