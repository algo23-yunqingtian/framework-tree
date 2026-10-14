# V87-RC1-G1 全量门禁脚本输出汇总

> **工单**: V87_RC1_G1_HERMES_FINAL_CLOSURE_REVIEW
> **日期**: 2026-10-14 14:55
> **分支**: feature/v87-rc1-g1 @ 8291c63

---

## 1. check_html.py 全量校验

| 项 | 结果 |
|---|---|
| 总页数 | 266 |
| PASS | 266 |
| FAIL | 0 |
| 结论 | ✅ **全部 PASS** |

校验项（每页 9 项）：
- 内容非空
- 字节≥12000
- chart 容器≥2
- chart-note≥2
- 全部 cid 已 __inst
- 公共 JS 完整
- 季节真数据历年 series 函数
- echarts.min.js 引用
- indicators_v1.json 版本

## 2. reclaim.py（历史遗留参考）

| 项 | 结果 |
|---|---|
| PASS | 9 |
| FAIL | 4 |
| 说明 | FAIL 均为 TD-V87-002 历史遗留 STATUS.md 线 A 表格契约缺失（Phase03~15），非本工单引入 |

## 3. 门禁基线确认

| 门禁 | 本次结果 | 历史基线 | 变化 |
|---|---|---|---|
| check_html | 266/266 PASS | 266/266 PASS | ✅ 一致 |
| reclaim | PASS=9 FAIL=4 | PASS=9 FAIL=4 | ✅ 一致（历史遗留） |

## 4. 结论

> **门禁全量执行全部 PASS，V87 收官归档无阻断项。**

---

**生成时间**: 2026-10-14 14:55
