# SKILL-WIND-EXCEL-WDF-BOOTSTRAP

Restored safe offline entrypoints for the P90A WDF bootstrap/controller test.

## Files

- `bootstrap_wdf.ps1` — dry-run bootstrap entrypoint, no live Wind calls
- `reset_wdf_safe.ps1` — agent-PID-scoped reset smoke helper
- `health_check_wdf.ps1` — lightweight folder health check

## Safety

- No WSD/WSS/WST calls
- No marker creation
- No REAL_WIND_CALL mutation
- No broad Excel cleanup
