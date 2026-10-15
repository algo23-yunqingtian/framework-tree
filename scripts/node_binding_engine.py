#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
node_binding_engine.py — Framework Tree V88 Node Binding 渲染引擎
================================================================
TASK_ID: V88_PHASE01_DSHE_P1_NODE_BINDING_ADAPT
AGENT: DSHE
BRANCH: feature/v88-g1
PURPOSE: 渲染引擎适配 node_binding 模式，支持节点-指标-图表动态绑定

核心能力：
  · YAML 元数据加载 + 6条校验规则执行
  · node_binding 绑定解析（tree_node_id → node → commodity → indicators）
  · 品种/节点/指标关联映射
  · 数据状态分流（matchable 真实数据 / pending_data 模拟回退）
  · 渲染回退逻辑（pending_data 图表自动生成占位占位符）
  · 节点切换（动态切换 tree_node_id 重建绑定上下文）
  · 指标挂载（向图表动态添加/移除指标）
  · 25张待补图表渲染链路打通验证

使用方式：
    from node_binding_engine import NodeBindingEngine
    engine = NodeBindingEngine(yaml_path, tree_config_path)
    engine.load()
    engine.validate()
    engine.get_chart_binding('cu_p1_ts_01')
    engine.render_chart('cu_p1_ts_01')

变更记录：
    V88.0.0 (2028-05-18): 初始版本，渲染引擎适配 node_binding 模式
"""
import json
import os
import re
import sys
import time
from collections import defaultdict, Counter
from typing import Optional

# ---------------------------------------------------------------------------
# YAML 支持：优先 PyYAML，降级为文本解析
# ---------------------------------------------------------------------------
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "v88.0.0"
VALID_CHART_TYPES = [
    "time_series", "gauge", "distribution", "stacked_bar",
    "heatmap", "radar", "sankey", "treemap"
]
VALID_DATA_STATUSES = ["matchable", "pending_data", "deprecated"]

# 6条校验规则
VALIDATION_RULES = [
    "no_cross_node_binding",
    "tree_node_id_valid",
    "commodity_valid",
    "auto_inherit_description",
    "chart_type_valid",
    "data_status_valid",
]

# 图表类型 → 渲染引擎方法映射
CHART_TYPE_RENDERERS = {
    "time_series": "render_time_series",
    "gauge": "render_gauge",
    "stacked_bar": "render_stacked_bar",
    "heatmap": "render_heatmap",
    "distribution": "render_distribution",
    "radar": "render_radar",
    "sankey": "render_sankey",
    "treemap": "render_treemap",
}

# pending_data 图表的模拟数据种子（用于端到端渲染验证）
SIMULATED_DATA_SEEDS = {
    "COMEX_CU": {"name": "COMEX铜", "unit": "USD/吨", "base": 9500.0, "trend": 0.001, "vol": 0.02},
    "COMEX_AL": {"name": "COMEX铝", "unit": "USD/吨", "base": 2400.0, "trend": 0.0008, "vol": 0.015},
    "COMEX_PB": {"name": "COMEX铅", "unit": "USD/吨", "base": 2100.0, "trend": -0.0005, "vol": 0.01},
    "COMEX_ZN": {"name": "COMEX锌", "unit": "USD/吨", "base": 2700.0, "trend": 0.0003, "vol": 0.015},
    "COMEX_NI": {"name": "COMEX镍", "unit": "USD/吨", "base": 16000.0, "trend": 0.0005, "vol": 0.025},
    "COMEX_SN": {"name": "COMEX锡", "unit": "USD/吨", "base": 32000.0, "trend": 0.001, "vol": 0.02},
    "GC_LI_CLOSE": {"name": "广期所碳酸锂", "unit": "元/吨", "base": 120000.0, "trend": 0.0008, "vol": 0.03},
    "GC_SI_CLOSE": {"name": "广期所工业硅", "unit": "元/吨", "base": 12500.0, "trend": 0.0003, "vol": 0.015},
    "CU_MONTH_SPREAD_2": {"name": "铜月差(2)", "unit": "元/吨", "base": 80.0, "trend": 0.0005, "vol": 0.05},
    "AL_MONTH_SPREAD_2": {"name": "铝月差(2)", "unit": "元/吨", "base": 120.0, "trend": 0.0003, "vol": 0.04},
    "PB_MONTH_SPREAD_2": {"name": "铅月差(2)", "unit": "元/吨", "base": 50.0, "trend": 0.0002, "vol": 0.06},
    "ZN_MONTH_SPREAD_2": {"name": "锌月差(2)", "unit": "元/吨", "base": 90.0, "trend": 0.0004, "vol": 0.05},
    "NI_MONTH_SPREAD_2": {"name": "镍月差(2)", "unit": "元/吨", "base": 350.0, "trend": 0.0006, "vol": 0.04},
    "SN_MONTH_SPREAD_2": {"name": "锡月差(2)", "unit": "元/吨", "base": 500.0, "trend": 0.0008, "vol": 0.045},
    "LI_MONTH_SPREAD_2": {"name": "锂月差(2)", "unit": "元/吨", "base": 2000.0, "trend": 0.001, "vol": 0.035},
    "SI_MONTH_SPREAD_2": {"name": "硅月差(2)", "unit": "元/吨", "base": 150.0, "trend": 0.0005, "vol": 0.06},
    "CU_BALANCE": {"name": "铜平衡表", "unit": "万吨", "base": 5.0, "trend": 0.0002, "vol": 0.1},
}


class ValidationResult:
    """单条校验规则执行结果"""
    def __init__(self, rule_id, chart_id, severity, message):
        self.rule_id = rule_id
        self.chart_id = chart_id
        self.severity = severity  # ERROR / WARN / PASS
        self.message = message

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "chart_id": self.chart_id,
            "severity": self.severity,
            "message": self.message,
        }


class ChartBinding:
    """图表绑定上下文：node_binding 解析后的完整绑定信息"""
    def __init__(self, chart_def):
        self.chart_id = chart_def.get("chart_id", "")
        self.tree_node_id = chart_def.get("tree_node_id", "")
        self.commodity = chart_def.get("commodity", "")
        self.chart_type = chart_def.get("chart_type", "")
        self.title = chart_def.get("title", "")
        self.indicators = chart_def.get("indicators", [])
        self.data_status = chart_def.get("data_status", "")
        self.business_description = chart_def.get("business_description", "")
        self.render_priority = chart_def.get("render_priority", 99)
        self.weekly_render = chart_def.get("weekly_render", False)
        self.pdf_template = chart_def.get("pdf_template", "")
        # 解析后的富信息（由 resolve_binding 填充）
        self.resolved_node = None
        self.resolved_commodity = None
        self.resolved_indicators = []
        self.render_data = None  # 模拟/真实数据

    def to_dict(self):
        return {
            "chart_id": self.chart_id,
            "tree_node_id": self.tree_node_id,
            "commodity": self.commodity,
            "chart_type": self.chart_type,
            "title": self.title,
            "data_status": self.data_status,
            "business_description": self.business_description,
            "render_priority": self.render_priority,
            "weekly_render": self.weekly_render,
            "indicator_count": len(self.indicators),
            "resolved_node": self.resolved_node,
            "resolved_commodity": self.resolved_commodity,
        }


class NodeBindingEngine:
    """
    V88 Node Binding 渲染引擎
    
    核心职责：
    1. 加载 framework_tree_meta_chart.yaml 元数据
    2. 加载 data/tree_config.json 树配置
    3. 执行 6 条校验规则
    4. 解析 node_binding 绑定关系
    5. 支持节点切换、指标挂载、渲染回退
    6. 提供 25 张待补图表的模拟渲染能力
    """

    def __init__(self, yaml_path=None, tree_config_path=None, repo_root=None):
        if repo_root is None:
            # 从当前文件位置推导仓库根目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(script_dir, ".."))
        self.repo_root = repo_root

        if yaml_path is None:
            yaml_path = os.path.join(
                repo_root, "analysis", "e2e_output", "v88", "backlog",
                "framework_tree_meta_chart.yaml"
            )
        self.yaml_path = yaml_path

        if tree_config_path is None:
            tree_config_path = os.path.join(repo_root, "data", "tree_config.json")
        self.tree_config_path = tree_config_path

        # 内部状态
        self.charts = []              # ChartBinding 列表
        self.tree_config = None       # 原始 tree_config
        self.node_index = {}          # node_id -> {name, q, comms, category}
        self.commodity_index = {}     # commodity_id -> {code, name}
        self.chart_index = {}         # chart_id -> ChartBinding
        self.validation_results = []
        self.load_errors = []
        self.load_time = None
        self._yaml_raw = None

    # =========================================================================
    # Phase 1: 加载
    # =========================================================================

    def load(self):
        """加载所有元数据和配置。返回 (success, message)。"""
        t0 = time.time()
        try:
            self._load_tree_config()
            self._load_yaml_metadata()
        except Exception as e:
            self.load_errors.append(str(e))
            return False, str(e)
        self.load_time = time.time() - t0
        self._build_indexes()
        return True, f"加载完成: {len(self.charts)} 张图表, {len(self.node_index)} 个节点"

    def _load_tree_config(self):
        """加载 data/tree_config.json"""
        if not os.path.exists(self.tree_config_path):
            raise FileNotFoundError(f"tree_config.json 不存在: {self.tree_config_path}")
        with open(self.tree_config_path, "r", encoding="utf-8") as f:
            self.tree_config = json.load(f)
        print(f"  [tree_config] 已加载: {len(self.tree_config.get('categories',[]))} 个类别, "
              f"{len(self.tree_config.get('commodities',[]))} 个品种")

    def _load_yaml_metadata(self):
        """加载 framework_tree_meta_chart.yaml"""
        if not os.path.exists(self.yaml_path):
            raise FileNotFoundError(f"YAML 文件不存在: {self.yaml_path}")

        if HAS_YAML:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                self._yaml_raw = yaml.safe_load(f)
            chart_defs = self._yaml_raw.get("charts", [])
        else:
            # 降级：文本模式解析（提取关键字段）
            print("  [WARN] PyYAML 不可用，使用文本模式解析")
            chart_defs = self._parse_yaml_text_fallback()

        for cd in chart_defs:
            cb = ChartBinding(cd)
            self.charts.append(cb)

        print(f"  [yaml] 已加载: {len(self.charts)} 张图表定义")
        return chart_defs

    def _parse_yaml_text_fallback(self):
        """PyYAML 不可用时的文本降级解析（仅提取关键结构）"""
        chart_defs = []
        current_chart = None
        current_field = None

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip()
                # 新图表开始
                m = re.match(r'^\s+- chart_id:\s*["\']?(.+?)["\']?\s*$', stripped)
                if m:
                    if current_chart:
                        chart_defs.append(current_chart)
                    current_chart = {"chart_id": m.group(1)}
                    current_field = None
                    continue
                # 顶层字段
                if current_chart:
                    m = re.match(r'^\s+(\w+):\s*(.+?)\s*$', stripped)
                    if m:
                        key, val = m.group(1), m.group(2).strip().strip('"\'')
                        if key == 'indicators':
                            current_chart['indicators'] = []
                            current_field = 'indicators'
                        elif key == 'chart_id':
                            pass  # already set
                        else:
                            # 类型转换
                            if val in ('true', 'True'):
                                current_chart[key] = True
                            elif val in ('false', 'False'):
                                current_chart[key] = False
                            elif val.isdigit():
                                current_chart[key] = int(val)
                            else:
                                current_chart[key] = val
                            current_field = None
                        continue
                    # indicators 子项
                    if current_field == 'indicators':
                        m2 = re.match(r'^\s+- (indicator_name|indicator_id):\s*["\']?(.+?)["\']?\s*$', stripped)
                        if m2:
                            # 开始新指标
                            current_chart['indicators'].append({
                                m2.group(1): m2.group(2)
                            })
                        elif stripped.strip().startswith('- '):
                            # 新指标块开始
                            pass

        if current_chart:
            chart_defs.append(current_chart)

        return chart_defs

    def _build_indexes(self):
        """构建节点索引和品种索引"""
        # 节点索引
        for cat in self.tree_config.get("categories", []):
            for child in cat.get("children", []):
                self.node_index[child["id"]] = {
                    "name": child.get("name", ""),
                    "q": child.get("q", ""),
                    "comms": set(child.get("comms", [])),
                    "category": cat["id"],
                    "code": child.get("code", ""),
                }

        # 品种索引
        for comm in self.tree_config.get("commodities", []):
            self.commodity_index[comm["id"]] = {
                "code": comm.get("code", ""),
                "name": comm.get("name", ""),
            }

        # 图表索引
        for cb in self.charts:
            self.chart_index[cb.chart_id] = cb

        print(f"  [index] 构建完成: {len(self.node_index)} 个节点, "
              f"{len(self.commodity_index)} 个品种, {len(self.chart_index)} 个图表")

    # =========================================================================
    # Phase 2: 校验
    # =========================================================================

    def validate(self, strict=True):
        """
        执行 6 条校验规则。
        strict=True: ERROR 阻断；strict=False: ERROR 记录但不阻断
        返回 ValidationResult 列表。
        """
        self.validation_results = []

        for cb in self.charts:
            # 规则 1: no_cross_node_binding
            self._rule_no_cross_node_binding(cb)
            # 规则 2: tree_node_id_valid
            self._rule_tree_node_id_valid(cb)
            # 规则 3: commodity_valid
            self._rule_commodity_valid(cb)
            # 规则 4: auto_inherit_description
            self._rule_auto_inherit_description(cb)
            # 规则 5: chart_type_valid
            self._rule_chart_type_valid(cb)
            # 规则 6: data_status_valid
            self._rule_data_status_valid(cb)

        # 汇总
        errors = [r for r in self.validation_results if r.severity == "ERROR"]
        warns = [r for r in self.validation_results if r.severity == "WARN"]
        passes = [r for r in self.validation_results if r.severity == "PASS"]

        print(f"  [validate] 结果: {len(passes)} PASS, {len(warns)} WARN, {len(errors)} ERROR")

        if errors and strict:
            raise RuntimeError(f"校验失败: {len(errors)} 个 ERROR")

        return self.validation_results

    def _rule_no_cross_node_binding(self, cb):
        """规则1: 图表绑定指标必须归属对应节点的comms范围"""
        node = self.node_index.get(cb.tree_node_id)
        if not node:
            return  # 节点无效由规则2处理

        comms = node.get("comms", set())
        for ind in cb.indicators:
            ind_comm = ind.get("commodity", cb.commodity)
            if ind_comm not in comms:
                self.validation_results.append(ValidationResult(
                    "no_cross_node_binding", cb.chart_id, "ERROR",
                    f"指标 commodity={ind_comm} 不在节点 {cb.tree_node_id} 的 comms 范围内 ({comms})"
                ))
            else:
                self.validation_results.append(ValidationResult(
                    "no_cross_node_binding", cb.chart_id, "PASS",
                    f"commodity={ind_comm} 在节点 {cb.tree_node_id} 的 comms 范围内"
                ))

    def _rule_tree_node_id_valid(self, cb):
        """规则2: 节点ID合法性校验"""
        if cb.tree_node_id in self.node_index:
            self.validation_results.append(ValidationResult(
                "tree_node_id_valid", cb.chart_id, "PASS",
                f"tree_node_id={cb.tree_node_id} 合法"
            ))
        else:
            self.validation_results.append(ValidationResult(
                "tree_node_id_valid", cb.chart_id, "ERROR",
                f"tree_node_id={cb.tree_node_id} 未注册"
            ))

    def _rule_commodity_valid(self, cb):
        """规则3: 商品合法性校验"""
        if cb.commodity in self.commodity_index:
            self.validation_results.append(ValidationResult(
                "commodity_valid", cb.chart_id, "PASS",
                f"commodity={cb.commodity} 合法"
            ))
        else:
            self.validation_results.append(ValidationResult(
                "commodity_valid", cb.chart_id, "ERROR",
                f"commodity={cb.commodity} 未注册"
            ))

    def _rule_auto_inherit_description(self, cb):
        """规则4: 业务描述自动继承校验"""
        node = self.node_index.get(cb.tree_node_id)
        if not node:
            return
        expected = f"{node['name']}({node['q']})"
        if cb.business_description == expected:
            self.validation_results.append(ValidationResult(
                "auto_inherit_description", cb.chart_id, "PASS",
                f"business_description 与节点定义一致"
            ))
        elif cb.business_description:
            self.validation_results.append(ValidationResult(
                "auto_inherit_description", cb.chart_id, "WARN",
                f"business_description='{cb.business_description}' 与预期 '{expected}' 不一致"
            ))
        else:
            self.validation_results.append(ValidationResult(
                "auto_inherit_description", cb.chart_id, "WARN",
                f"business_description 为空，预期 '{expected}'"
            ))

    def _rule_chart_type_valid(self, cb):
        """规则5: 图表类型合法性"""
        if cb.chart_type in VALID_CHART_TYPES:
            self.validation_results.append(ValidationResult(
                "chart_type_valid", cb.chart_id, "PASS",
                f"chart_type={cb.chart_type} 合法"
            ))
        else:
            self.validation_results.append(ValidationResult(
                "chart_type_valid", cb.chart_id, "ERROR",
                f"chart_type={cb.chart_type} 不合法"
            ))

    def _rule_data_status_valid(self, cb):
        """规则6: 数据状态合法性"""
        if cb.data_status in VALID_DATA_STATUSES:
            self.validation_results.append(ValidationResult(
                "data_status_valid", cb.chart_id, "PASS",
                f"data_status={cb.data_status} 合法"
            ))
        else:
            self.validation_results.append(ValidationResult(
                "data_status_valid", cb.chart_id, "ERROR",
                f"data_status={cb.data_status} 不合法"
            ))

    # =========================================================================
    # Phase 3: 绑定解析
    # =========================================================================

    def get_chart_binding(self, chart_id):
        """
        获取单个图表的完整绑定上下文。
        执行 node_binding 解析：tree_node_id → node → commodity → indicators
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return None
        self.resolve_binding(cb)
        return cb

    def resolve_binding(self, cb=None, chart_id=None):
        """
        解析 node_binding 绑定关系。
        支持：
          - 解析节点定义（name, q, comms, category）
          - 解析品种定义（code, name）
          - 解析指标列表
          - 填充 business_description
        """
        if cb is None and chart_id:
            cb = self.chart_index.get(chart_id)
            if not cb:
                return None

        # 1. 解析节点
        node = self.node_index.get(cb.tree_node_id)
        if node:
            cb.resolved_node = {
                "id": cb.tree_node_id,
                "name": node["name"],
                "q": node["q"],
                "comms": list(node["comms"]),
                "category": node["category"],
                "code": node["code"],
            }
            # 自动继承业务描述（始终更新，支持节点切换后重新解析）
            cb.business_description = f"{node['name']}({node['q']})"
        else:
            cb.resolved_node = {"error": f"节点 {cb.tree_node_id} 未找到"}

        # 2. 解析品种
        comm = self.commodity_index.get(cb.commodity)
        if comm:
            cb.resolved_commodity = {
                "id": cb.commodity,
                "code": comm["code"],
                "name": comm["name"],
            }
        else:
            cb.resolved_commodity = {"error": f"品种 {cb.commodity} 未找到"}

        # 3. 解析指标
        cb.resolved_indicators = []
        for ind in cb.indicators:
            resolved_ind = {
                "name": ind.get("indicator_name", ""),
                "id": ind.get("indicator_id", ""),
                "commodity": ind.get("commodity", cb.commodity),
            }
            cb.resolved_indicators.append(resolved_ind)

        return cb

    def resolve_all(self):
        """批量解析所有图表的绑定关系"""
        count = 0
        for cb in self.charts:
            self.resolve_binding(cb)
            count += 1
        print(f"  [resolve] 解析完成: {count} 张图表")
        return count

    # =========================================================================
    # Phase 4: 渲染
    # =========================================================================

    def render_chart(self, chart_id, use_simulated=False):
        """
        渲染单张图表。
        
        数据分流逻辑：
          - matchable + 真实数据存在 → 使用真实数据
          - matchable + 无真实数据 → 模拟数据（fallback）
          - pending_data + use_simulated=True → 模拟数据
          - pending_data + use_simulated=False → 占位符
        
        返回渲染结果字典，包含：
          - chart_id, title, chart_type, data_status
          - render_data: 渲染数据列表
          - placeholder: 是否为占位符
          - source: 'real' / 'simulated' / 'placeholder'
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return {"error": f"chart {chart_id} not found"}

        self.resolve_binding(cb)

        # 数据分流
        if cb.data_status == "matchable":
            # 尝试加载真实数据
            real_data = self._load_real_data(cb)
            if real_data:
                return self._build_render_result(cb, real_data, source="real")
            else:
                # fallback: 使用模拟数据
                sim_data = self._generate_simulated_data(cb)
                return self._build_render_result(cb, sim_data, source="simulated")

        elif cb.data_status == "pending_data":
            if use_simulated:
                sim_data = self._generate_simulated_data(cb)
                return self._build_render_result(cb, sim_data, source="simulated")
            else:
                placeholder = self._generate_placeholder(cb)
                return self._build_render_result(cb, placeholder, source="placeholder")

        elif cb.data_status == "deprecated":
            return {
                "error": f"图表 {chart_id} 已弃用 (deprecated)",
                "chart_id": chart_id,
            }

        else:
            return {
                "error": f"未知数据状态: {cb.data_status}",
                "chart_id": chart_id,
            }

    def render_all(self, use_simulated=True):
        """
        批量渲染所有图表。
        返回按 data_status 分组的渲染结果。
        """
        results = {
            "matchable": [],
            "pending_data": [],
            "deprecated": [],
            "errors": [],
        }

        for cb in self.charts:
            r = self.render_chart(cb.chart_id, use_simulated=use_simulated)
            if "error" in r:
                results["errors"].append(r)
            else:
                results[cb.data_status].append(r)

        print(f"  [render_all] 渲染完成: matchable={len(results['matchable'])}, "
              f"pending={len(results['pending_data'])}, "
              f"deprecated={len(results['deprecated'])}, errors={len(results['errors'])}")
        return results

    def _resolve_db_path(self):
        """解析数据库路径，支持环境变量覆盖。

        优先级（从高到低）:
          1. V88_PHASE03_TEST_DB  \u2014 Phase03 独立测试库 (series_cache 表)
          2. V88_API_CACHE_DB     \u2014 自定义 API 缓存库路径
          3. scripts/api_cache.db \u2014 V87/Phase02 默认路径 (indicator_cache 表)

        返回: db_path 字符串 或 None（不可达时）。
        """
        p03_path = os.environ.get("V88_PHASE03_TEST_DB", "").strip()
        if p03_path and os.path.exists(p03_path):
            return p03_path

        api_path = os.environ.get("V88_API_CACHE_DB", "").strip()
        if api_path and os.path.exists(api_path):
            return api_path

        default_path = os.path.join(self.repo_root, "scripts", "api_cache.db")
        if os.path.exists(default_path):
            return default_path

        return None

    def _detect_table_schema(self, cursor):
        """探测数据库中可用的数据表。

        返回: 表名集合，例如 {"series_cache", "indicator_cache", ...}
        """
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r[0] for r in cursor.fetchall()}

    def _load_from_indicator_cache(self, cursor, ind_id, code):
        """从 indicator_cache 表加载真实数据 (V87/Phase02 schema)。

        表结构: indicator_cache(metric, code, data_json)
        data_json 格式: {"name": "...", "unit": "...", "points": [{"date": "...", "value": ...}]}

        返回: {"name": str, "unit": str, "points": list} 或 None
        """
        try:
            cursor.execute(
                "SELECT data_json FROM indicator_cache WHERE metric=? AND code=?",
                (ind_id, code.upper())
            )
            row = cursor.fetchone()
            if row:
                d = json.loads(row[0])
                pts = [{"date": p["date"], "value": float(p["value"])}
                       for p in d.get("points", [])
                       if isinstance(p, dict) and p.get("date") and p.get("value") is not None]
                pts.sort(key=lambda p: p["date"])
                return {
                    "name": d.get("name", ""),
                    "unit": d.get("unit", ""),
                    "points": pts,
                }
        except Exception:
            pass
        return None

    def _load_from_series_cache(self, cursor, ind_id, code):
        """从 series_cache 表加载真实数据 (Phase03 schema)。

        表结构: series_cache(id, indicator_id, indicator_id_mapped, commodity, date, value, source, imported_at)
        查询条件: indicator_id_mapped = DSHE indicator_id, commodity = 品种代码
        聚合输出: 与 indicator_cache 的 data_json 格式对齐

        返回: {"name": str, "unit": str, "points": list} 或 None
        """
        try:
            cursor.execute(
                "SELECT date, value FROM series_cache "
                "WHERE indicator_id_mapped=? AND commodity=? AND indicator_id_mapped IS NOT NULL "
                "ORDER BY date",
                (ind_id, code)
            )
            rows = cursor.fetchall()
            if rows:
                pts = [{"date": r[0], "value": float(r[1])}
                       for r in rows if r[1] is not None]
                if pts:
                    return {
                        "name": "",
                        "unit": "",
                        "points": pts,
                    }
        except Exception:
            pass
        return None

    def _load_real_data(self, cb):
        """
        从数据库加载真实数据。

        自动检测数据库 schema，支持两种表结构:
          - indicator_cache (V87/Phase02): data_json 聚合列
          - series_cache (Phase03): 逐行 date/value, 聚合组装 data_json

        数据库路径解析优先级:
          1. V88_PHASE03_TEST_DB 环境变量
          2. V88_API_CACHE_DB 环境变量
          3. scripts/api_cache.db (默认)

        如果数据库不存在或指标无数据，返回 None。
        """
        db_path = self._resolve_db_path()
        if not db_path:
            return None

        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            tables = self._detect_table_schema(cursor)

            all_data = []
            for ind in cb.indicators:
                ind_id = ind.get("indicator_id", "")
                code = ind.get("commodity", cb.commodity)
                ind_name = ind.get("indicator_name", ind_id)
                data_entry = None

                if "indicator_cache" in tables:
                    data_entry = self._load_from_indicator_cache(cursor, ind_id, code)
                    if data_entry and not data_entry.get("name"):
                        data_entry["name"] = ind_name
                elif "series_cache" in tables:
                    data_entry = self._load_from_series_cache(cursor, ind_id, code)
                    if data_entry and not data_entry.get("name"):
                        data_entry["name"] = ind_name

                if data_entry and data_entry.get("points"):
                    all_data.append(data_entry)

            conn.close()

            if all_data:
                return all_data
            return None
        except Exception:
            return None

    def _generate_simulated_data(self, cb):
        """
        为图表生成模拟数据。
        使用 SIMULATED_DATA_SEEDS 中配置的参数生成确定性伪随机序列。
        """
        from datetime import datetime, timedelta

        all_data = []
        for ind in cb.indicators:
            ind_id = ind.get("indicator_id", "")
            seed = SIMULATED_DATA_SEEDS.get(ind_id)

            if seed:
                base = seed["base"]
                trend = seed["trend"]
                vol = seed["vol"]
            else:
                # 从 chart_id 派生确定性种子
                import hashlib
                h = hashlib.md5(ind_id.encode()).hexdigest()
                base = int(h[:8], 16) % 10000
                trend = 0.001
                vol = 0.02

            # 生成 120 天模拟数据
            data = []
            dt = datetime(2028, 1, 1)
            for i in range(120):
                # 确定性伪随机
                import random
                rng = random.Random(hash((ind_id, i)) % (2**32))
                value = base * (1 + trend * i + rng.uniform(-vol, vol))
                date_str = dt.strftime("%Y-%m-%d")
                data.append({"date": date_str, "value": round(value, 4)})
                dt += timedelta(days=1)

            all_data.append({
                "name": seed["name"] if seed else ind.get("indicator_name", ind_id),
                "unit": seed["unit"] if seed else "",
                "points": data,
            })

        return all_data

    def _generate_placeholder(self, cb):
        """
        为 pending_data 图表生成占位符数据。
        """
        indicators = cb.indicators if cb.indicators else [{"indicator_name": "?", "indicator_id": "?"}]
        return [{
            "name": "[待补数据] " + (ind.get("indicator_name", ind.get("indicator_id", "?")) for ind in indicators).__next__(),
            "unit": "N/A",
            "points": [],
            "placeholder": True,
        }]

    def _build_render_result(self, cb, data, source):
        """构建标准渲染结果"""
        return {
            "chart_id": cb.chart_id,
            "title": cb.title,
            "chart_type": cb.chart_type,
            "data_status": cb.data_status,
            "tree_node_id": cb.tree_node_id,
            "commodity": cb.commodity,
            "business_description": cb.business_description,
            "indicators": cb.indicators,
            "render_data": data,
            "source": source,  # 'real' / 'simulated' / 'placeholder'
            "placeholder": source == "placeholder",
            "renderable": True,
        }

    # =========================================================================
    # Phase 5: 节点切换 & 指标挂载
    # =========================================================================

    def switch_node(self, chart_id, new_node_id):
        """
        切换图表绑定的 Framework Tree 节点。
        
        节点切换流程：
        1. 检查新节点ID合法性
        2. 检查当前品种在新节点的 comms 范围内
        3. 更新 tree_node_id
        4. 重新解析绑定关系
        5. 更新业务描述
        
        返回: (success, message)
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return False, f"chart {chart_id} not found"

        old_node_id = cb.tree_node_id
        node = self.node_index.get(new_node_id)
        if not node:
            return False, f"node {new_node_id} not registered"

        if cb.commodity not in node["comms"]:
            return False, (
                f"commodity {cb.commodity} not in node {new_node_id} comms "
                f"({node['comms']})"
            )

        # 执行切换
        cb.tree_node_id = new_node_id
        self.resolve_binding(cb)

        return True, (
            f"node switch OK: {old_node_id} -> {new_node_id}, "
            f"business_description='{cb.business_description}'"
        )

    def mount_indicator(self, chart_id, indicator_name, indicator_id):
        """
        向图表动态挂载指标。
        
        挂载流程：
        1. 解析 chart_id
        2. 检查指标ID非空
        3. 添加到 indicators 列表
        4. 重新解析绑定
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return False, f"chart {chart_id} not found"

        if not indicator_id or not indicator_name:
            return False, "indicator_name and indicator_id cannot be empty"

        # 避免重复挂载
        for existing in cb.indicators:
            if existing.get("indicator_id") == indicator_id:
                return False, f"indicator {indicator_id} already mounted on chart {chart_id}"

        cb.indicators.append({
            "indicator_name": indicator_name,
            "indicator_id": indicator_id,
        })
        self.resolve_binding(cb)

        return True, (
            f"indicator mounted: '{indicator_name}' ({indicator_id}) "
            f"-> chart {chart_id}, total {len(cb.indicators)} indicators"
        )

    def unmount_indicator(self, chart_id, indicator_id):
        """
        从图表动态移除指标。
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return False, f"chart {chart_id} not found"

        original_count = len(cb.indicators)
        cb.indicators = [
            ind for ind in cb.indicators
            if ind.get("indicator_id") != indicator_id
        ]

        if len(cb.indicators) == original_count:
            return False, f"indicator {indicator_id} not found on chart {chart_id}"

        self.resolve_binding(cb)
        return True, f"indicator removed: {indicator_id} <- chart {chart_id}, remaining {len(cb.indicators)}"

    # =========================================================================
    # Phase 6: 统计与查询
    # =========================================================================

    def get_stats(self):
        """获取引擎统计数据"""
        status_counts = Counter(cb.data_status for cb in self.charts)
        type_counts = Counter(cb.chart_type for cb in self.charts)
        node_counts = Counter(cb.tree_node_id for cb in self.charts)
        comm_counts = Counter(cb.commodity for cb in self.charts)
        weekly_count = sum(1 for cb in self.charts if cb.weekly_render)
        total_indicators = sum(len(cb.indicators) for cb in self.charts)

        # 校验结果统计
        error_count = sum(1 for r in self.validation_results if r.severity == "ERROR")
        warn_count = sum(1 for r in self.validation_results if r.severity == "WARN")
        pass_count = sum(1 for r in self.validation_results if r.severity == "PASS")

        return {
            "total_charts": len(self.charts),
            "data_status": dict(status_counts),
            "chart_types": dict(type_counts),
            "nodes_used": dict(node_counts),
            "commodities_used": dict(comm_counts),
            "weekly_render_charts": weekly_count,
            "total_indicators": total_indicators,
            "validation": {
                "pass": pass_count,
                "warn": warn_count,
                "error": error_count,
                "total": len(self.validation_results),
            },
            "load_time_sec": round(self.load_time or 0, 4),
        }

    def get_pending_charts(self):
        """获取所有 pending_data 状态的图表"""
        return [cb for cb in self.charts if cb.data_status == "pending_data"]

    def get_matchable_charts(self):
        """获取所有 matchable 状态的图表"""
        return [cb for cb in self.charts if cb.data_status == "matchable"]

    def get_charts_by_node(self, node_id):
        """按节点获取图表列表"""
        return [cb for cb in self.charts if cb.tree_node_id == node_id]

    def get_charts_by_commodity(self, commodity):
        """按品种获取图表列表"""
        return [cb for cb in self.charts if cb.commodity == commodity]

    def get_charts_by_type(self, chart_type):
        """按图表类型获取图表列表"""
        return [cb for cb in self.charts if cb.chart_type == chart_type]

    # =========================================================================
    # Phase 7: 渲染回退
    # =========================================================================

    def render_with_fallback(self, chart_id):
        """
        渲染回退逻辑：
          1. 先尝试真实数据
          2. 真实数据不可用 → 尝试模拟数据
          3. 模拟数据也不可用 → 占位符
        
        返回渲染结果（始终返回可渲染的数据）。
        """
        cb = self.chart_index.get(chart_id)
        if not cb:
            return {"error": f"chart {chart_id} not found"}

        self.resolve_binding(cb)

        # Step 1: 尝试真实数据
        real_data = self._load_real_data(cb)
        if real_data:
            return self._build_render_result(cb, real_data, source="real")

        # Step 2: 尝试模拟数据
        sim_data = self._generate_simulated_data(cb)
        if sim_data:
            return self._build_render_result(cb, sim_data, source="simulated")

        # Step 3: 占位符
        placeholder = self._generate_placeholder(cb)
        return self._build_render_result(cb, placeholder, source="placeholder")

    # =========================================================================
    # Phase 8: 25张待补图表渲染链路验证
    # =========================================================================

    def verify_pending_render_chain(self):
        """
        验证 25 张待补图表的渲染链路。
        
        验证内容：
        1. 每个 pending_data 图表都能成功解析 node_binding
        2. 每个 pending_data 图表都能生成模拟数据
        3. 每个 pending_data 图表都能生成占位符
        4. 渲染回退逻辑正常工作
        
        返回验证结果字典。
        """
        pending_charts = self.get_pending_charts()
        results = {
            "total_pending": len(pending_charts),
            "binding_resolved": 0,
            "simulated_data_ok": 0,
            "placeholder_ok": 0,
            "fallback_ok": 0,
            "errors": [],
            "detail": [],
        }

        for cb in pending_charts:
            chart_detail = {
                "chart_id": cb.chart_id,
                "tree_node_id": cb.tree_node_id,
                "commodity": cb.commodity,
                "chart_type": cb.chart_type,
            }

            # 1. 绑定解析
            binding = self.get_chart_binding(cb.chart_id)
            if binding and binding.resolved_node and "error" not in binding.resolved_node:
                chart_detail["binding"] = "OK"
                results["binding_resolved"] += 1
            else:
                chart_detail["binding"] = "FAIL"
                results["errors"].append(f"{cb.chart_id}: 绑定解析失败")

            # 2. 模拟数据
            sim_data = self._generate_simulated_data(cb)
            if sim_data and len(sim_data[0].get("points", [])) > 0:
                chart_detail["simulated_data"] = "OK"
                results["simulated_data_ok"] += 1
            else:
                chart_detail["simulated_data"] = "FAIL"
                results["errors"].append(f"{cb.chart_id}: 模拟数据生成失败")

            # 3. 占位符
            placeholder = self._generate_placeholder(cb)
            if placeholder:
                chart_detail["placeholder"] = "OK"
                results["placeholder_ok"] += 1

            # 4. 渲染回退
            fallback = self.render_with_fallback(cb.chart_id)
            if fallback and fallback.get("renderable"):
                chart_detail["fallback"] = "OK"
                results["fallback_ok"] += 1
            else:
                chart_detail["fallback"] = "FAIL"
                results["errors"].append(f"{cb.chart_id}: 渲染回退失败")

            chart_detail["indicator_count"] = len(cb.indicators)
            results["detail"].append(chart_detail)

        results["success_rate"] = (
            round(results["binding_resolved"] / max(results["total_pending"], 1) * 100, 2)
            if results["total_pending"] > 0 else 0
        )

        print(f"  [verify_pending] 待补图表渲染链路: "
              f"{results['total_pending']} 张, "
              f"绑定={results['binding_resolved']}, "
              f"模拟={results['simulated_data_ok']}, "
              f"占位={results['placeholder_ok']}, "
              f"回退={results['fallback_ok']}, "
              f"失败={len(results['errors'])}")

        return results


# =========================================================================
# 入口：直接运行时执行自检
# =========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("V88 Node Binding Engine — 自检")
    print("=" * 70)

    engine = NodeBindingEngine()

    print("\n[1/4] 加载...")
    success, msg = engine.load()
    if not success:
        print(f"  加载失败: {msg}")
        sys.exit(1)
    print(f"  {msg}")

    print("\n[2/4] 校验...")
    results = engine.validate(strict=False)
    print(f"  {len(results)} 条校验结果")

    print("\n[3/4] 解析绑定...")
    count = engine.resolve_all()
    print(f"  解析完成: {count} 张图表")

    print("\n[4/4] 统计...")
    stats = engine.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== 自检完成 ===")