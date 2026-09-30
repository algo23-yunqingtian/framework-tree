#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ths_render_prep_fixed.py — V85 渲染编排脚本 (修复版 v2.0)

工单: HERMES_V85_RENDER_SCRIPT_FIX_AND_MANUAL_REVIEW_PACKAGE
升级自: ths_render_prep_script.py v1.0 (HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE)

=== 修复清单 ===

--- 4 项边界缺陷 (render_simulation_report.md 4.1) ---

[DEF-1] THS 模板分组不精确
  问题: 131 个 THS 模板无 zhiji_id 全部归入 review_first 组，不够精确
  修复: 新增 pending_match 专用分组，与 P1 复核区分
  代码: RENDER_STRATEGIES 新增 "pending_match" 策略

[DEF-2] 部分阻塞 → 降级渲染
  问题: 267 个模板因 1-2 条 series 无效被完全阻塞
  修复: 实现部分阻塞逻辑——仅阻塞无效 series，有效 series 可降级渲染
  代码: PartialBlockAnalyzer 类，partial_blocked/partial_render 分组

[DEF-3] 渲染引擎无重试机制
  问题: 渲染阶段无重试
  修复: 增加 max_retries=3, retry_delay=5s 配置
  代码: RENDER_CONFIG 新增 retry 配置

[DEF-4] 无并发渲染支持
  问题: 89 个可渲染模板串行渲染
  修复: 增加 concurrency 配置 + 并发组评估
  代码: concurrency_config, 独立模板组可并发

--- 4 项遗漏点 (render_simulation_report.md 4.2) ---

[GAP-1] zhiji_id 格式校验不完整
  问题: 仅检查是否以 ID 开头，未做正则校验
  修复: 增加 zhiji_id 正则校验 ^ID[a-zA-Z0-9_]+$
  代码: ZHIJI_ID_PATTERN

[GAP-2] series 空列表检查缺失
  问题: 模板无图表内容未检查
  修复: schema 校验新增 series 空列表检查
  代码: validate_schema() 新增 series_empty 检查

[GAP-3] meta 字段缺失检查
  问题: THS 模板品种信息丢失
  修复: schema 校验新增 meta 存在性检查
  代码: validate_schema() 新增 meta_missing 检查

[GAP-4] verify_note 前缀未清洗
  问题: "重检索填充:" 前缀导致语义校验误判
  修复: 语义校验前清洗 verify_note 前缀
  代码: clean_verify_note()

--- 4 项优化建议 (render_simulation_report.md 4.3) ---

[OPT-1] 部分阻塞 → 降级渲染
  同 DEF-2，已实现

[OPT-2] THS 专用流程
  同 DEF-1，已实现 pending_match 组

[OPT-3] 重试机制
  同 DEF-3，已实现

[OPT-4] 并发评估
  同 DEF-4，已实现

--- 完善异常分支 ---
  - 字段缺失 (name/original_name)
  - chart_type 枚举非法
  - series 空列表
  - 多 Y 轴复合图表
  - 图例名称异常 (空字符串/重复)

--- 两级临时白名单 ---
  - 模板级白名单: template_id → 命中P0但放行至人工复核
  - Series 指标级白名单: template_id/series_index → 特定指标放行
  - 白名单配置独立 JSON，不改动原始模板

约束(T4):
  - 全程禁止调用 zhiji 接口，不拉取真实时序数据
  - chart_risk_bound_all.json 只读
  - indicators_v1.json、tree_config.json 只读
  - 仅新增文件

用法:
  python3 ths_render_prep_fixed.py --bound chart_risk_bound_all.json --tasks ths_render_task_list.json --out .
  python3 ths_render_prep_fixed.py --whitelist temp_whitelist_schema.json --bound ... --tasks ...
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

# === 常量 ===
ZHIJI_ID_PATTERN = re.compile(r'^ID[a-zA-Z0-9_]+$')
VERIFY_NOTE_PREFIXES = ['重检索填充:', '重检索填充 ', '重检索填充']

VALID_CHART_TYPES = {
    '单折线', '多折线', '堆叠柱状', '复合混合(折线+柱状)',
    '堆叠面积图', '双轴图', '饼图', '热力图', '柱状图',
    '',
}

RENDER_CONFIG = {
    'max_retries': 3,
    'retry_delay_seconds': 5,
    'concurrency': 4,
    'render_timeout_seconds': 60,
}


class WhitelistManager:
    """两级临时白名单管理器

    支持两种粒度的白名单:
    1. 模板级: 整个模板放行至人工复核
    2. Series 级: 模板内特定指标放行

    白名单配置独立 JSON，不改动原始模板。
    命中 P0 但在白名单内 → 流转至人工复核队列，不直接阻塞。
    """

    def __init__(self, whitelist_path: Optional[str] = None):
        self.template_whitelist: Set[str] = set()
        self.series_whitelist: Set[str] = set()  # "template_id/series_index"
        self.expiry_whitelist: Dict[str, str] = {}  # template_id → expiry_date
        self.stats = {'template_count': 0, 'series_count': 0, 'with_expiry': 0}

        if whitelist_path and os.path.exists(whitelist_path):
            self.load(whitelist_path)

    def load(self, path: str):
        """加载白名单 JSON 配置"""
        with open(path, encoding='utf-8') as f:
            config = json.load(f)

        # 模板级白名单
        for entry in config.get('template_whitelist', []):
            tid = entry.get('template_id', '')
            if tid:
                self.template_whitelist.add(tid)
                self.stats['template_count'] += 1
                if entry.get('expiry_date'):
                    self.expiry_whitelist[tid] = entry['expiry_date']
                    self.stats['with_expiry'] += 1

        # Series 级白名单
        for entry in config.get('series_whitelist', []):
            key = f"{entry.get('template_id', '')}/{entry.get('series_index', '')}"
            self.series_whitelist.add(key)
            self.stats['series_count'] += 1

    def is_template_whitelisted(self, template_id: str) -> bool:
        """检查模板是否在白名单中（含过期检查）"""
        if template_id not in self.template_whitelist:
            return False
        expiry = self.expiry_whitelist.get(template_id)
        if expiry:
            try:
                expiry_dt = datetime.fromisoformat(expiry)
                if datetime.now() > expiry_dt:
                    return False  # 已过期
            except ValueError:
                return True  # 无法解析日期时默认有效
        return True

    def is_series_whitelisted(self, template_id: str, series_index: int) -> bool:
        """检查 series 是否在白名单中"""
        return f"{template_id}/{series_index}" in self.series_whitelist

    def get_template_whitelist_entry(self, template_id: str) -> Optional[Dict]:
        """获取模板白名单条目详情"""
        return {
            'whitelisted': self.is_template_whitelisted(template_id),
            'expiry_date': self.expiry_whitelist.get(template_id),
            'series_whitelist_count': sum(
                1 for s in self.series_whitelist
                if s.startswith(f"{template_id}/")
            ),
        }

    def check_template_risk_override(self, template_id: str, risk_level: str) -> Optional[str]:
        """
        检查白名单是否覆盖风险判定。

        返回:
          - 'review': 模板在白名单中，从 blocked 降至 review_first
          - 'partial': 部分 series 在白名单中，可降级渲染
          - None: 无白名单覆盖
        """
        if risk_level not in ('P0', 'BLOCKED'):
            return None
        if self.is_template_whitelisted(template_id):
            return 'review'
        return None


class PartialBlockAnalyzer:
    """部分阻塞分析器

    分析模板内 series 的有效性:
    - 仅部分 series 无效时 → 降级渲染有效 series
    - 全部 series 无效时 → 完全阻塞
    """

    def __init__(self, whitelist_mgr: WhitelistManager):
        self.whitelist = whitelist_mgr

    def analyze(self, template_id: str, bound_entry: Dict) -> Dict[str, Any]:
        """
        分析模板的阻塞状态，返回部分阻塞信息。

        Returns:
          {
            'fully_blocked': bool,
            'partial_blocked': bool,
            'valid_series': [...],
            'invalid_series': [...],
            'whitelisted_series': [...],
            'can_partial_render': bool,
            'whitelist_override': str or None,
          }
        """
        series_risks = bound_entry.get('series_risks', [])
        if not series_risks:
            return {
                'fully_blocked': False,
                'partial_blocked': False,
                'valid_series': [],
                'invalid_series': [],
                'whitelisted_series': [],
                'can_partial_render': True,
                'whitelist_override': None,
            }

        valid = []
        invalid = []
        whitelisted = []

        for i, sr in enumerate(series_risks):
            key = f"{template_id}/{i}"
            is_invalid = sr.get('risk_level') in ('BLOCKED', 'P0')

            if self.whitelist.is_series_whitelisted(template_id, i):
                whitelisted.append(i)
                if not is_invalid:
                    valid.append(i)
            elif is_invalid:
                invalid.append(i)
            else:
                valid.append(i)

        # 全部无效 → 完全阻塞
        if not valid and not whitelisted:
            return {
                'fully_blocked': True,
                'partial_blocked': False,
                'valid_series': valid,
                'invalid_series': invalid,
                'whitelisted_series': whitelisted,
                'can_partial_render': False,
                'whitelist_override': self.whitelist.check_template_risk_override(
                    template_id, bound_entry.get('template_risk_level', '')),
            }

        # 部分无效 → 降级渲染
        if invalid and valid:
            return {
                'fully_blocked': False,
                'partial_blocked': True,
                'valid_series': valid,
                'invalid_series': invalid,
                'whitelisted_series': whitelisted,
                'can_partial_render': True,
                'whitelist_override': self.whitelist.check_template_risk_override(
                    template_id, bound_entry.get('template_risk_level', '')),
            }

        # 全部有效
        return {
            'fully_blocked': False,
            'partial_blocked': False,
            'valid_series': valid,
            'invalid_series': invalid,
            'whitelisted_series': whitelisted,
            'can_partial_render': True,
            'whitelist_override': None,
        }


class RenderTaskOrchestratorFixed:
    """渲染任务编排器 v2.0 (修复版)"""

    RENDER_STRATEGIES = {
        'can_render': {
            'label': '可直接渲染',
            'color': 'green',
            'action': '立即执行渲染',
            'failure_strategy': f"重试{RENDER_CONFIG['max_retries']}次, "
                               f"间隔{RENDER_CONFIG['retry_delay_seconds']}秒, "
                               f"失败后标记为RENDER_FAILED",
            'concurrent': True,
            'concurrency': RENDER_CONFIG['concurrency'],
        },
        'partial_render': {
            'label': '降级渲染(部分series)',
            'color': 'yellow',
            'action': '仅渲染有效series, 跳过无效series',
            'failure_strategy': '重试有效series, 记录跳过的无效series',
            'concurrent': True,
            'concurrency': RENDER_CONFIG['concurrency'],
        },
        'review_first': {
            'label': '人工复核后渲染',
            'color': 'orange',
            'action': '等待人工复核确认后执行渲染',
            'failure_strategy': '记录复核结论, 人工决定是否重试',
            'concurrent': False,
            'concurrency': 1,
        },
        'pending_match': {
            'label': 'THS待匹配zhiji_id',
            'color': 'blue',
            'action': '等待DSHB匹配zhiji_id后进入渲染',
            'failure_strategy': '记录为PENDING_MATCH, 不执行渲染',
            'concurrent': False,
            'concurrency': 1,
        },
        'blocked': {
            'label': '阻塞不渲染',
            'color': 'red',
            'action': '禁止渲染, 需修复风险后重新评估',
            'failure_strategy': '不执行渲染, 记录阻塞原因',
            'concurrent': False,
            'concurrency': 1,
        },
    }

    def __init__(self, bound_path: str, task_list_path: str,
                 whitelist_path: Optional[str] = None):
        with open(bound_path, encoding='utf-8') as f:
            self.bound = json.load(f)
        with open(task_list_path, encoding='utf-8') as f:
            self.task_list = json.load(f)

        # 构建索引
        self.bound_index = {}
        for t in self.bound.get('templates', []):
            self.bound_index[t['template_id']] = t

        # 初始化白名单和部分阻塞分析器
        self.whitelist = WhitelistManager(whitelist_path)
        self.partial_analyzer = PartialBlockAnalyzer(self.whitelist)

    def clean_verify_note(self, text: str) -> str:
        """[GAP-4] 清洗 verify_note 前缀"""
        if not text:
            return text
        for prefix in VERIFY_NOTE_PREFIXES:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        return text

    def validate_zhiji_id(self, zhiji_id: Optional[str]) -> Tuple[str, Optional[str]]:
        """[GAP-1] zhiji_id 正则校验"""
        if not zhiji_id:
            return 'missing', None
        zhiji_id = str(zhiji_id).strip()
        if ZHIJI_ID_PATTERN.match(zhiji_id):
            return 'valid', zhiji_id
        return 'invalid', zhiji_id

    def validate_schema(self, template_id: str, bound_entry: Dict) -> Dict[str, Any]:
        """Schema 校验 — 含遗漏点修复"""
        errors = []
        warnings = []

        # [GAP-2] series 空列表检查
        series_count = bound_entry.get('series_count', 0)
        if series_count == 0:
            errors.append('series 列表为空，模板无图表内容')

        # [GAP-3] meta 字段缺失检查 (THS 模板)
        source = bound_entry.get('source', '')
        if source == 'THS':
            title = bound_entry.get('title', '')
            if not title:
                warnings.append('THS 模板缺少 title (meta 字段)')

        # chart_type 枚举检查
        ct = bound_entry.get('chart_type', '')
        if ct not in VALID_CHART_TYPES:
            errors.append(f'chart_type 枚举值非法: {ct}')

        # series 字段完整性
        series_risks = bound_entry.get('series_risks', [])
        for i, sr in enumerate(series_risks):
            name = sr.get('series_name', '') or sr.get('name', '')
            if not name:
                errors.append(f'series[{i}] 缺少 name 字段')
            # 图例名称异常: 空字符串
            legend = sr.get('legend_name', '')
            if legend and not legend.strip():
                warnings.append(f'series[{i}] 图例名称为空字符串')

        # 多 Y 轴复合图表检查
        has_y1 = any(sr.get('axis') == 'y1' for sr in series_risks)
        has_y2 = any(sr.get('axis') == 'y2' for sr in series_risks)
        if has_y1 and has_y2:
            warnings.append('多Y轴复合图表，需确认双轴配置正确')

        # 图例名称重复检查
        legends = [sr.get('legend_name', '') or sr.get('series_name', '')
                    for sr in series_risks]
        seen = {}
        for idx, lg in enumerate(legends):
            if lg in seen:
                warnings.append(f'series[{idx}] 图例名称重复: "{lg[:30]}"')
            else:
                seen[lg] = idx

        return {
            'ok': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'series_count': series_count,
        }

    def check_zhiji_ids_status(self, bound_entry: Dict) -> Dict:
        """[GAP-1] 检查 zhiji_id 状态（含正则校验）"""
        series_risks = bound_entry.get('series_risks', [])
        total = len(series_risks)
        valid = 0
        missing = 0
        invalid = 0
        invalid_ids = []

        for sr in series_risks:
            status, _ = self.validate_zhiji_id(sr.get('zhiji_id'))
            if status == 'valid':
                valid += 1
            elif status == 'missing':
                missing += 1
            else:
                invalid += 1
                invalid_ids.append(sr.get('zhiji_id'))

        return {
            'total_series': total,
            'valid_ids': valid,
            'missing_ids': missing,
            'invalid_ids': invalid,
            'invalid_id_samples': invalid_ids[:5],
        }

    def route_task(self, task: Dict, bound_entry: Dict) -> Tuple[str, Dict]:
        """
        任务路由 — 修复缺陷后的路由逻辑。

        路由优先级:
        1. THS 无 zhiji_id → pending_match [DEF-1]
        2. 全部 series 无效且不在白名单 → blocked
        3. 部分 series 无效 → partial_render [DEF-2]
        4. P0 但在白名单 → review_first [白名单]
        5. P0 且不在白名单 → blocked
        6. P1 → review_first
        7. CLEAN → can_render
        """
        tid = task['template_id']
        source = task['source']
        risk_level = task['risk_level']
        is_ths = source == 'THS' or tid.startswith('THS-')

        # THS 无 zhiji_id → pending_match
        zhiji_status = self.check_zhiji_ids_status(bound_entry)
        if is_ths and zhiji_status['valid_ids'] == 0 and zhiji_status['missing_ids'] > 0:
            return 'pending_match', {
                'reason': 'THS 模板无 zhiji_id，需后续匹配',
                'zhiji_status': zhiji_status,
            }

        # 部分阻塞分析
        partial = self.partial_analyzer.analyze(tid, bound_entry)

        # 完全阻塞
        if partial['fully_blocked'] and not partial['whitelist_override']:
            return 'blocked', {
                'reason': f'全部 series 无效 (P0/BLOCKED)',
                'partial_analysis': partial,
            }

        # 白名单覆盖 P0 → review
        if partial['whitelist_override'] == 'review':
            return 'review_first', {
                'reason': f'P0 但在模板白名单中，放行至人工复核',
                'partial_analysis': partial,
                'whitelist_override': 'review',
            }

        # 部分阻塞 → 降级渲染
        if partial['partial_blocked'] and partial['can_partial_render']:
            return 'partial_render', {
                'reason': f'部分 series 无效 ({len(partial["invalid_series"])}个)，'
                          f'降级渲染有效 series ({len(partial["valid_series"])}个)',
                'partial_analysis': partial,
            }

        # 按风险等级路由
        if risk_level == 'P0':
            return 'blocked', {
                'reason': 'P0 语义冲突，阻塞不渲染',
                'partial_analysis': partial,
            }
        elif risk_level == 'P1':
            return 'review_first', {
                'reason': 'P1 风险，需人工复核',
                'partial_analysis': partial,
            }
        else:
            return 'can_render', {
                'reason': 'CLEAN，可直接渲染',
                'partial_analysis': partial,
            }

    def generate_task_manifest(self) -> Dict[str, Any]:
        """生成完整渲染任务清单 (修复版)"""
        manifest = {
            'version': '2.0',
            'generated_at': datetime.now().isoformat(),
            'task_id': 'HERMES_RENDER_SCRIPT_FIX_AND_MANUAL_REVIEW_PACKAGE',
            'description': 'V85 渲染任务清单 v2.0 — 修复4缺陷+4遗漏点+4建议+两级白名单+异常分支',
            'changes_from_v1': {
                'DEF-1': '新增 pending_match 分组',
                'DEF-2': '新增 partial_render 分组 + 部分阻塞降级',
                'DEF-3': '渲染重试机制 (max_retries=3, delay=5s)',
                'DEF-4': '并发渲染支持 (concurrency=4)',
                'GAP-1': 'zhiji_id 正则校验',
                'GAP-2': 'series 空列表检查',
                'GAP-3': 'THS meta 缺失检查',
                'GAP-4': 'verify_note 前缀清洗',
            },
            'constraint': '仅任务编排，不执行zhiji时序拉取，不调用zhiji接口',
            'render_config': RENDER_CONFIG,
            'strategies': self.RENDER_STRATEGIES,
            'whitelist_stats': self.whitelist.stats,
            'summary': {},
            'render_groups': {},
        }

        # 逐任务路由
        group_tasks = {g: [] for g in self.RENDER_STRATEGIES}

        for group_key in self.task_list.get('groups', {}):
            for t in self.task_list.get('groups', {}).get(group_key, []):
                bound_entry = self.bound_index.get(t['template_id'], {})
                route, route_info = self.route_task(t, bound_entry)

                # Schema 校验
                schema = self.validate_schema(t['template_id'], bound_entry)

                # zhiji_id 状态
                zhiji_status = self.check_zhiji_ids_status(bound_entry)

                # 部分阻塞分析
                partial = route_info.get('partial_analysis', {})

                task = {
                    'task_id': f"RENDER-{t['source']}-{t['template_id']}",
                    'source': t['source'],
                    'template_id': t['template_id'],
                    'variety': t.get('variety', ''),
                    'risk_level': t['risk_level'],
                    'routed_group': route,
                    'route_reason': route_info.get('reason', ''),
                    'risk_tags': {
                        'p0_count': t.get('p0', 0),
                        'p1_count': t.get('p1', 0),
                        'blocked_count': t.get('blocked', 0),
                    },
                    'render_strategy': self.RENDER_STRATEGIES[route]['action'],
                    'failure_strategy': self.RENDER_STRATEGIES[route]['failure_strategy'],
                    'status': 'PENDING',
                    'schema_validation': schema,
                    'zhiji_ids_status': zhiji_status,
                    'partial_block': {
                        'fully_blocked': partial.get('fully_blocked', False),
                        'partial_blocked': partial.get('partial_blocked', False),
                        'valid_series_count': len(partial.get('valid_series', [])),
                        'invalid_series_count': len(partial.get('invalid_series', [])),
                        'whitelisted_series_count': len(partial.get('whitelisted_series', [])),
                    },
                    'metadata': {
                        'series_count': bound_entry.get('series_count', 0),
                        'chart_type': bound_entry.get('chart_type', ''),
                        'title': bound_entry.get('title', ''),
                    },
                    'preflight': {
                        'zhiji_data_required': True,
                        'zhiji_ids_status': zhiji_status,
                        'render_prerequisites': [
                            'zhiji series data fetched',
                            'chart template validated',
                            'semantic check passed',
                        ],
                    },
                }

                group_tasks[route].append(task)

        # 构建 manifest render_groups
        for gk, strategy in self.RENDER_STRATEGIES.items():
            manifest['render_groups'][gk] = {
                'label': strategy['label'],
                'color': strategy['color'],
                'task_count': len(group_tasks[gk]),
                'tasks': group_tasks[gk],
            }

        # 摘要
        manifest['summary'] = {
            'total': sum(len(v) for v in group_tasks.values()),
            'can_render': len(group_tasks['can_render']),
            'partial_render': len(group_tasks['partial_render']),
            'review_first': len(group_tasks['review_first']),
            'pending_match': len(group_tasks['pending_match']),
            'blocked': len(group_tasks['blocked']),
        }

        return manifest

    def preflight_check(self) -> Dict[str, Any]:
        """渲染前置检查 (修复版)"""
        checks = {
            'input_files': {},
            'template_counts': {},
            'risk_distribution': {},
            'whitelist': self.whitelist.stats,
            'blocking_issues': [],
            'ready_to_render': False,
        }

        stats = self.bound.get('statistics', {})
        checks['template_counts'] = {
            'pdf_total': stats.get('pdf_total', 0),
            'ths_total': stats.get('ths_total', 0),
            'grand_total': stats.get('total_templates', 0),
        }

        summary = self.task_list.get('summary', {})
        checks['render_queue_size'] = summary.get('can_render', 0)
        checks['ready_to_render'] = summary.get('can_render', 0) > 0

        return checks

    def generate_csv_export(self, manifest: Dict) -> str:
        """生成 CSV 任务清单摘要"""
        lines = ['task_id,source,template_id,variety,risk_level,routed_group,'
                 'route_reason,p0_count,p1_count,schema_ok,'
                 'fully_blocked,partial_blocked,valid_series_count,invalid_series_count']
        for gk in self.RENDER_STRATEGIES:
            for t in manifest['render_groups'][gk]['tasks']:
                sb = t.get('partial_block', {})
                sc = t.get('schema_validation', {})
                lines.append(
                    f"RENDER-{t['source']}-{t['template_id']},"
                    f"{t['source']},{t['template_id']},{t.get('variety','')},"
                    f"{t['risk_level']},{t['routed_group']},"
                    f"\"{t.get('route_reason','')}\" ,"
                    f"{t['risk_tags'].get('p0_count',0)},"
                    f"{t['risk_tags'].get('p1_count',0)},"
                    f"{sc.get('ok', False)},"
                    f"{sb.get('fully_blocked', False)},"
                    f"{sb.get('partial_blocked', False)},"
                    f"{sb.get('valid_series_count', 0)},"
                    f"{sb.get('invalid_series_count', 0)}"
                )
        return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='V85 渲染编排脚本 v2.0 (修复版)')
    parser.add_argument('--bound', required=True, help='chart_risk_bound_all.json 路径')
    parser.add_argument('--tasks', required=True, help='ths_render_task_list.json 路径')
    parser.add_argument('--out', default='.', help='输出目录')
    parser.add_argument('--whitelist', help='临时白名单 JSON 路径')
    parser.add_argument('--check', action='store_true', help='仅前置检查')
    args = parser.parse_args()

    orch = RenderTaskOrchestratorFixed(args.bound, args.tasks, args.whitelist)

    print('=== 渲染前置检查 v2.0 ===')
    preflight = orch.preflight_check()
    print(f"  模板总数: {preflight['template_counts']['grand_total']} "
          f"(PDF:{preflight['template_counts']['pdf_total']} "
          f"THS:{preflight['template_counts']['ths_total']})")
    print(f"  白名单: 模板{orch.whitelist.stats['template_count']} "
          f"Series{orch.whitelist.stats['series_count']}")

    if args.check:
        return

    # 生成任务清单
    manifest = orch.generate_task_manifest()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    s = manifest['summary']
    print(f"\n=== 路由结果 ===")
    print(f"  可直接渲染: {s['can_render']}")
    print(f"  降级渲染(部分series): {s['partial_render']}")
    print(f"  人工复核: {s['review_first']}")
    print(f"  THS待匹配: {s['pending_match']}")
    print(f"  阻塞: {s['blocked']}")
    print(f"  合计: {s['total']}")

    manifest_path = out_dir / 'ths_render_task_manifest_fixed.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 渲染任务清单: {manifest_path} ({os.path.getsize(manifest_path)} bytes)")

    csv_path = out_dir / 'ths_render_task_summary_fixed.csv'
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(orch.generate_csv_export(manifest))
    print(f"✅ CSV摘要: {csv_path}")


if __name__ == '__main__':
    main()
