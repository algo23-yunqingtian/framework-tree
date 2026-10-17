# HERMES Global Arbiter Archive — MD5 Manifest

> **TASK_ID**: V88_PHASE03_P6_HERMESHF_GLOBAL_ARBITER_STANDBY_JOB / T6
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **GENERATED**: 2026-10-17T13:00 +0800

---

## P6 交付物

| # | 文件 | MD5 | 大小 |
|---|------|-----|------|
| 1 | `global_asset_watch_shturl` | `B8F1917F37149B05506B67F99C9B51E0` | 4370B |
| 2 | `arbiter_logic_lock_confirm.md` | `09C0675EA35C6A84C71D7433A03E697C` | 4824B |
| 3 | `link_status_poll_shturl` | `73ABE583A1B6BA9478BD96393198E8DA` | 2515B |
| 4 | `triparty_weekly_sanity_check.md` | `818196FCB70F7016C6B22D3BE3E4BCB1` | 4545B |
| 5 | `exemption_followup_v4.md` | `9499B6DCB246B2C67CA0AC03406EBA18` | 3919B |
| 6 | `phase04_bootstrap_freeze_confirm.md` | `2A3791E4E02105B5858E94404BBE2D1E` | 3384B |

## 脚本修复（守卫性）

| # | 文件 | 修复内容 | 新 MD5 |
|---|------|---------|--------|
| 7 | `opt_auth_guard/official_trigger_arbiter.py` | 路径基数（dirname 两层→一层） | `CD64A06D7DC643DF7EA97F7E4D61AD21` |
| 8 | `analysis/.../phase03_summary/phase04_boot_precheck.py` | 路径基数（dirname 两层→`.git` 向上查找） | `8178B5724C07D1E2C77975616565205F` |
