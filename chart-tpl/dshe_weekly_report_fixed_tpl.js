/**
 * =============================================================================
 * DSHE Gate Harden V88 周报图表固定 ECharts Option 模板
 * =============================================================================
 * TASK_ID: V88_PHASE03_P3_DSHE_GATE_LOCK_METRICSDB_SEED_JOB
 * AGENT: DSHE | BRANCH: feature/v88-g1
 * GENERATED: 2026-10-16T23:55
 *
 * 🚨 构图锁定声明:
 *   此模板构图锁定。更新只替换 series/data 字段。
 *   禁止改动 option 顶层布局、grid、xAxis/yAxis、legend、tooltip、
 *   color、fontFamily、fontSize、padding、barWidth、itemStyle、
 *   lineStyle、areaStyle、label、markPoint、markLine 等布局相关配置。
 *   如需修改布局，必须新建模板版本，不得修改本文件。
 *
 * 📋 构图包含:
 *   1. 横向任务进度条 (ProgressBar)
 *   2. 关键指标卡片 (KPI Cards)
 *   3. 状态仪表盘 (Status Gauges)
 *
 * 🔄 仅替换以下字段:
 *   - series[0].data — 进度条数据
 *   - series[1].data — 仪表盘数据
 *   - series[2].data — 门禁状态数据
 *   - title — 标题文字
 *   - graphic.elements[].children[].style.text — 指标值文本
 * =============================================================================
 */

// ===========================================================================
// 固定配置 — 禁止修改
// ===========================================================================

var DSHE_WEEKLY_REPORT_FIXED_TPL = {

  // === 全局配色 (固定) ===
  color: ['#1890FF', '#52C41A', '#FAAD14', '#F5222D', '#722ED1', '#13C2C2'],

  // === 全局字体 (固定) ===
  textStyle: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif',
    color: '#262626'
  },

  // === 标题 (固定) ===
  title: {
    text: 'DSHE V88 周报 — Gate Harden P0-12 终版',
    subtext: '2026-10-16 | Triple-Seal Complete | Engine Frozen',
    left: 'center',
    top: 8,
    textStyle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: '#262626'
    },
    subtextStyle: {
      fontSize: 12,
      color: '#8C8C8C'
    }
  },

  // === 图形元素 — 关键指标卡片 (固定布局) ===
  graphic: {
    elements: [
      // === 卡片1: 稳态CPU ===
      {
        type: 'group',
        left: 20,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#F0F5FF', stroke: '#ADC6FF', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: '稳态CPU',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '0.0654%',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#1890FF'
            }
          },
          {
            type: 'text',
            style: {
              text: '↓ 96.2% vs 阈值',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#52C41A'
            }
          }
        ]
      },
      // === 卡片2: R3 E2E ===
      {
        type: 'group',
        left: 172,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#F6FFED', stroke: '#B7EB8F', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: 'R3 E2E',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '8/8',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#52C41A'
            }
          },
          {
            type: 'text',
            style: {
              text: '100% PASS',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#52C41A'
            }
          }
        ]
      },
      // === 卡片3: D7覆盖率 ===
      {
        type: 'group',
        left: 324,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#FFFBE6', stroke: '#FFE58F', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: 'D7 覆盖率',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '98.57%',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#FAAD14'
            }
          },
          {
            type: 'text',
            style: {
              text: '69/70 指标渲染',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#FAAD14'
            }
          }
        ]
      },
      // === 卡片4: P99延迟 ===
      {
        type: 'group',
        left: 476,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#F9F0FF', stroke: '#D3ADF7', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: 'P99 延迟',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '449.3ms',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#722ED1'
            }
          },
          {
            type: 'text',
            style: {
              text: '↓ 13.1% vs pre-opt',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#52C41A'
            }
          }
        ]
      },
      // === 卡片5: 约束合规 ===
      {
        type: 'group',
        left: 628,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#E6FFFB', stroke: '#87E8DE', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: '约束合规',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '11/11',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#13C2C2'
            }
          },
          {
            type: 'text',
            style: {
              text: '✓ 全链路合规',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#52C41A'
            }
          }
        ]
      },
      // === 卡片6: 密封层数 ===
      {
        type: 'group',
        left: 780,
        top: 50,
        z: 10,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 140, height: 70, r: 8 },
            style: { fill: '#FFF2F0', stroke: '#FFCCC7', lineWidth: 1 }
          },
          {
            type: 'text',
            style: {
              text: '密封层数',
              x: 12, y: 8,
              fontSize: 11,
              fill: '#8C8C8C'
            }
          },
          {
            type: 'text',
            style: {
              text: '3 层',
              x: 12, y: 24,
              fontSize: 22,
              fontWeight: 'bold',
              fill: '#F5222D'
            }
          },
          {
            type: 'text',
            style: {
              text: 'MD5+SHA256+独立',
              x: 12, y: 52,
              fontSize: 10,
              fill: '#52C41A'
            }
          }
        ]
      }
    ]
  },

  // === Grid 布局 (固定) ===
  grid: [
    {
      left: 20,
      right: 20,
      top: 140,
      height: 100,
      containLabel: true
    },
    {
      left: 20,
      right: 20,
      top: 260,
      height: 80,
      containLabel: true
    },
    {
      left: 20,
      right: 20,
      top: 360,
      height: 80,
      containLabel: true
    }
  ],

  // === X轴 (固定) ===
  xAxis: [
    {
      type: 'category',
      gridIndex: 0,
      data: ['稳态CPU达标', 'R3 E2E回归', 'D7覆盖率', 'P99延迟', '约束合规', '三门密封'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        color: '#595959',
        interval: 0,
        margin: 8
      }
    },
    {
      type: 'category',
      gridIndex: 1,
      data: ['引擎冻结', 'CPU口径', '归档完整', '零污染'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        color: '#595959',
        interval: 0
      }
    },
    {
      type: 'category',
      gridIndex: 2,
      data: ['P0-12 Gate', 'Native PASS', 'Phase04准备'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        color: '#595959',
        interval: 0
      }
    }
  ],

  // === Y轴 (固定) ===
  yAxis: [
    {
      type: 'value',
      gridIndex: 0,
      max: 100,
      show: false
    },
    {
      type: 'value',
      gridIndex: 1,
      max: 100,
      show: false
    },
    {
      type: 'value',
      gridIndex: 2,
      max: 2,
      show: false
    }
  ],

  // === Tooltip (固定) ===
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderColor: '#E8E8E8',
    borderWidth: 1,
    textStyle: { fontSize: 12, color: '#262626' }
  },

  // === Series — 仅替换 data 字段 ===
  series: [
    // === Series 0: 横向任务进度条 ===
    {
      name: '任务进度',
      type: 'bar',
      gridIndex: 0,
      barWidth: 24,
      barCategoryGap: '40%',
      itemStyle: {
        borderRadius: [4, 4, 4, 4]
      },
      data: [
        { value: 100, itemStyle: { color: '#52C41A' } },
        { value: 100, itemStyle: { color: '#52C41A' } },
        { value: 98.57, itemStyle: { color: '#52C41A' } },
        { value: 90.14, itemStyle: { color: '#52C41A' } },
        { value: 100, itemStyle: { color: '#52C41A' } },
        { value: 100, itemStyle: { color: '#52C41A' } }
      ],
      label: {
        show: true,
        position: 'right',
        formatter: '{c}%',
        fontSize: 10,
        fontWeight: 'bold',
        color: '#262626'
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#FAAD14', width: 1 },
        data: [{ yAxis: 90 }],
        label: { show: false }
      }
    },

    // === Series 1: 状态仪表盘 ===
    {
      name: '状态仪表盘',
      type: 'gauge',
      gridIndex: 1,
      radius: '85%',
      center: ['12.5%', '50%'],
      startAngle: 90,
      endAngle: -270,
      min: 0,
      max: 100,
      progress: { show: true, width: 8, roundCap: true },
      axisLine: {
        lineStyle: { width: 8, color: [[1, '#F0F0F0']] }
      },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        fontSize: 18,
        fontWeight: 'bold',
        offsetCenter: [0, '0%']
      },
      data: [
        { value: 100, name: '引擎冻结', title: { offsetCenter: [0, '35%'] } },
        { value: 100, name: 'CPU口径', title: { offsetCenter: [0, '35%'] } },
        { value: 100, name: '归档完整', title: { offsetCenter: [0, '35%'] } },
        { value: 100, name: '零污染', title: { offsetCenter: [0, '35%'] } }
      ],
      title: {
        fontSize: 10,
        color: '#8C8C8C',
        offsetCenter: [0, '60%']
      }
    },

    // === Series 2: 门禁状态 ===
    {
      name: '门禁状态',
      type: 'gauge',
      gridIndex: 2,
      radius: '85%',
      center: ['16.7%', '50%'],
      startAngle: 90,
      endAngle: -270,
      min: 0,
      max: 2,
      progress: { show: true, width: 8, roundCap: true },
      axisLine: {
        lineStyle: { width: 8, color: [[1, '#F0F0F0']] }
      },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: false,
        formatter: function(value) {
          if (value === 2) return '✅ 通过';
          if (value === 1) return '⏳ 等待';
          return '🔒 锁定';
        },
        fontSize: 14,
        fontWeight: 'bold',
        offsetCenter: [0, '0%']
      },
      data: [
        { value: 2, name: 'P0-12 Gate' },
        { value: 2, name: 'Native PASS' },
        { value: 0, name: 'Phase04准备' }
      ],
      title: {
        fontSize: 10,
        color: '#8C8C8C',
        offsetCenter: [0, '60%']
      }
    }
  ]
};

// ===========================================================================
// 使用指南
// ===========================================================================
//
// 1. 加载:
//    var chart = echarts.init(document.getElementById('chart'));
//    chart.setOption(DSHE_WEEKLY_REPORT_FIXED_TPL);
//
// 2. 更新数据 (仅替换 data 字段):
//    chart.setOption({
//      series: [
//        { name: '任务进度', data: [newData0, ...] },
//        { name: '状态仪表盘', data: [newData1, ...] },
//        { name: '门禁状态', data: [newData2, ...] }
//      ]
//    });
//
// 3. 🚨 禁止修改以下字段 (构图锁定):
//    - color
//    - textStyle
//    - title
//    - graphic
//    - grid
//    - xAxis
//    - yAxis
//    - tooltip
//    - series[0].barWidth
//    - series[0].itemStyle.borderRadius
//    - series[0].label
//    - series[0].markLine
//    - series[1].radius / center / startAngle / endAngle / min / max
//    - series[1].progress / axisLine / pointer / axisTick / splitLine / axisLabel / detail / title
//    - series[2].radius / center / startAngle / endAngle / min / max
//    - series[2].progress / axisLine / pointer / axisTick / splitLine / axisLabel / detail / title
//
// 4. 如需修改构图: 创建新模板文件 (dshe_weekly_report_fixed_tpl_v2.js)
//
// ===========================================================================