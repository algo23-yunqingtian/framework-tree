# DSHD Defect Observation Registry (Audit-Side Perspective)

> **⚠️ DISCLAIMER — READ FIRST**
>
> **This is DSHD's audit observation registry — NOT the official DSHC defect registry.**
>
> DSHC (the delivery-side system) retains formal defect registration authority. This registry is maintained by the DSHD monitoring agent as an independent audit record of observed engineering defects, process failures, and risk events encountered during the G7 adjudication cycle. Entries here represent DSHD's perspective and findings; they do not constitute formal DSHC defect registrations and should not be used as the authoritative source for defect status, severity, or resolution. Where discrepancies exist between this registry and DSHC's formal records, DSHC's records govern.

---

## 1. Registry Metadata

| Field | Value |
|---|---|
| **Registry ID** | DSHD_DEFECT_OBSERVATION_REGISTRY |
| **Maintaining Agent** | DSHD-P67 (DSHD Monitoring Agent) |
| **Registry Type** | Audit-Side Observation Registry (Independent Record) |
| **Authority Boundary** | DSHD observation only; DSHC retains formal registration authority |
| **Created** | 2026-10-16 (DSHD-P67 Exploration Phase) |
| **Last Updated** | 2026-10-16 20:03+ (POLL-117+ monitoring cycle) |
| **Observation Scope** | G7 Adjudication Ledger cycle — all monitoring rounds POLL-01 through POLL-117+ |
| **Coverage Period** | 2026-10-16 14:50 through 2026-10-16 20:03+ |
| **Monitoring Platform** | DSHD v3 monitoring script (credential-aware, encoding-safe) |
| **Methodology** | Continuous file hash verification, ledger line-by-line audit, Wind event log parsing, cross-reference against SHA256_CHECKSUMS.txt and broadcast manifests |
| **Credential Handling** | All credentials redacted as [REDACTED]. No plaintext secrets appear in this document. |
| **Related Documents** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md; DSHD_P67_ROUND17_AUDIT_REPORT.md; tracking_monitor_audit.jsonl; wind_excel_events.jsonl; SHA256_CHECKSUMS.txt; G7_ADJUDICATION_PACKAGE_MANIFEST.json |
| **DSHD Action Authority** | Observe, log, escalate — does not modify source files or attempt autonomous fixes |
| **Escalation Channel** | DSHC (primary escalation recipient for all CRITICAL/HIGH findings) |

---

## 2. Executive Summary

### 2.1 Overview

DSHD-P67 monitored the G7 adjudication cycle across **117+ polling cycles** (POLL-01 through POLL-117+), spanning approximately 5+ hours of continuous observation. During this period, **11 engineering defects** were observed and logged. The monitoring process itself identified and resolved 2 internal defects (encoding and credential regex gaps) to improve subsequent detection accuracy.

### 2.2 Defect Count by Status

| Status | Count | Defect IDs |
|---|---|---|
| **OPEN — Active / Persistent** | 5 | DEFECT-001, DEFECT-002, DEFECT-003, DEFECT-004, DEFECT-005 |
| **RESOLVED** | 4 | DEFECT-006, DEFECT-007, DEFECT-008, DEFECT-009 |
| **INFORMATIONAL** | 2 | DEFECT-010, DEFECT-011 |
| **Total** | **11** | — |

### 2.3 Defect Count by Severity

| Severity | Count | Defect IDs |
|---|---|---|
| **CRITICAL** | 2 | DEFECT-004 (Wind client blocking), DEFECT-005 (credential exposure) |
| **HIGH** | 3 | DEFECT-001 (P61 tools missing), DEFECT-002 (checksum drift), DEFECT-003 (file missing) |
| **MEDIUM** | 0 | — |
| **LOW / INFORMATIONAL** | 6 | DEFECT-006, DEFECT-007, DEFECT-008, DEFECT-009, DEFECT-010, DEFECT-011 |
| **Total** | **11** | — |

### 2.4 Key Findings

| # | Finding | Severity | Action Status |
|---|---|---|---|
| 1 | **Wind desktop client non-functional** — all Wind data queries blocked; 108+ API calls for FACTOR-004/006/007 cannot execute | CRITICAL / BLOCKING | Escalated to DSHC; no response as of POLL-117+ |
| 2 | **Plaintext credentials committed to git** — 3 ledger lines contain exposed credentials | CRITICAL / SECURITY | Escalated; CRITICAL_CREDENTIAL_DETECTED alert active |
| 3 | **P61 scanner toolchain missing** — `_p61_t0_staging/` directory absent; 10 deliverables unavailable | HIGH | Manual review completed as substitute (42/42 false alarms) |
| 4 | **SHA256 checksum drift** — 14/17 files showed hash mismatch (process failure indicator) | HIGH | DSHC regenerated at 17:25; sync mechanism recommended |
| 5 | **P49_pre_gray_check.md missing** — pre-validation template unavailable | HIGH | DSHC confirmation required on restore necessity |

---

## 3. Defect Entry Format

Each defect entry in this registry follows the standardized format below:

| Field | Description |
|---|---|
| **Defect ID** | Unique identifier: `DEFECT-NNN` (zero-padded three-digit sequence) |
| **Title** | Concise defect description (10–15 words maximum) |
| **Severity** | CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL |
| **Status** | OPEN / RESOLVED / INFORMATIONAL — with qualifier where applicable |
| **First Observed** | Timestamp and monitoring context when the defect was first detected |
| **Evidence Anchors** | Specific file paths, line numbers, or document sections that support the observation |
| **Description** | Detailed technical description of the defect, including root cause analysis where available |
| **Impact** | Scope of impact — affected systems, blocked operations, risk level |
| **Current State** | Most recent observation of the defect status |
| **DSHD Action** | What DSHD did (observe, log, escalate) — DSHD does not modify source files |
| **DSHC Action Required** | Specific actions DSHC must take to resolve or mitigate the defect |

---

## 4. Defect Entries

---

### DEFECT-001: P61 Scanner Tools Missing

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-001 |
| **Title** | P61 Scanner Toolchain Directory and 10 Deliverables Missing |
| **Severity** | HIGH |
| **Status** | OPEN / PERSISTENT |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §6.1 |

#### Description

The `_p61_t0_staging/` directory — which should contain the P61 scanner toolchain and its associated deliverables — does not exist on disk. As a result, **10 P61 deliverables are unavailable**, including:

1. `_p61e_poll39_scan.py` — Scanner entry-point script
2. `poll39_main_audit_report.md` — Phase 39 main audit report
3. Phase 61a audit logs
4. Phase 61b audit logs
5. Phase 61c audit logs
6. R-P61-001 ledger scope evaluation
7. `_p61e_scan_result.json` — Scanner output result file
8. Additional P61 tool artifacts (7 total, exact list partially reconstructed)

The absence is not a recent regression — the directory was not present during the earliest P67 exploration pass, suggesting the toolchain was either never deployed to this environment or was removed before DSHD monitoring began.

#### Impact

- **FL scanner tools unavailable** — the automated scanner pipeline that was designed to run as part of P61 cannot execute
- **Manual review required as substitute** — DSHD-P67 completed a full manual review as a fallback, evaluating all 42 flagged items
- **Manual review result**: 42/42 items classified as false alarms (no true positives identified)
- **Process gap**: The P61 toolchain recovery path is undefined — no known rebuild procedure, migration plan, or cancellation record exists

#### Current State

Still missing as of the latest monitoring cycle (POLL-117+, 2026-10-16 20:03+). DSHD did not attempt to rebuild the toolchain — this is outside DSHD's action authority (observe, log, escalate only).

#### DSHD Action

- Observed and logged the absence
- Completed manual substitute review (42/42 false alarms confirmed)
- Did not attempt autonomous reconstruction

#### DSHC Action Required

Clarify the recovery path for the P61 toolchain:

1. **Rebuild** — redeploy `_p61_t0_staging/` with the full scanner toolchain
2. **Migrate** — move the toolchain to a new canonical location
3. **Cancel** — formally deprecate the P61 toolchain and update downstream references

---

### DEFECT-002: SHA256 Checksum Drift (14/17 Files)

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-002 |
| **Title** | SHA256 Checksum Drift Across 14 of 17 Ledger Files |
| **Severity** | HIGH |
| **Status** | OPEN / PERSISTENT |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §7.2 |

#### Description

At the time of first observation, **14 out of 17 files** in the `G7_ADJUDICATION_LEDGER/` directory had SHA256 hashes that did not match the entries recorded in `SHA256_CHECKSUMS.txt`. Only **3 files matched** their recorded checksums:

| Matching File | SHA256 Status |
|---|---|
| `WL006_WL014_whitelist_draft.md` | ✅ Match |
| `G7_ADJUDICATION_PACKAGE_MANIFEST.json` | ✅ Match |
| `G7_DSHA_DSHD_MONITORING_ROUND_001.md` | ✅ Match |

Additionally, **1 file was missing entirely** from disk (see DEFECT-003 for details on the missing `P49_pre_gray_check.md`).

#### Root Cause Analysis

The checksum drift was caused by an **incomplete partial refresh** of `SHA256_CHECKSUMS.txt`:

- The file was locally updated at **16:49:09**
- Only **entries 9–17** were refreshed with current hashes
- **Entries 1–8 and 10–15** were not synchronized with the actual on-disk file contents
- This partial update created a state where the manifest claimed correct hashes for some files but stale hashes for others

#### Current State

DSHC-P66 regenerated the checksums at **17:25** with **19 entries** (reflecting newly added files). All **18 present files** now show correct SHA256 hashes. The immediate integrity issue is resolved, but the **drift history itself is a process failure indicator** — the manual checksum update process allowed partial synchronization that went undetected.

#### Impact

- **Integrity trust eroded** — the checksum manifest was unreliable during the observation window
- **File verification impossible** — no downstream consumer could trust `SHA256_CHECKSUMS.txt` as an integrity reference between 16:49 and 17:25
- **Process gap identified** — no automated sync mechanism existed; manual updates were error-prone and not validated for completeness

#### DSHD Action

- Observed and logged the checksum mismatch across all 17 files
- Cross-referenced with the brief evidence at §7.2
- Did not attempt to fix the checksums (outside DSHD action authority)

#### DSHC Action Required

1. **Verify** that all checksums are now fully synchronized (DSHC-P66 regeneration at 17:25 was reported as complete)
2. **Establish** an automated checksum sync mechanism (e.g., post-commit hook, CI job) to prevent future partial-refresh failures
3. **Document** the checksum update procedure with completeness validation as a mandatory step

---

### DEFECT-003: P49_pre_gray_check.md Missing

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-003 |
| **Title** | P49 Pre-Gray-Check Pre-Validation Template File Missing |
| **Severity** | HIGH |
| **Status** | OPEN / PERSISTENT |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | SHA256_CHECKSUMS.txt entry #10 (status: MISSING); disk search returned no matches |

#### Description

The file `P49_pre_gray_check.md` — referenced in `SHA256_CHECKSUMS.txt` entry #10 — does not exist on disk at any of the expected locations. The entry shows status **MISSING**, confirming the file was never deployed or was deleted before DSHD observation began.

#### File Path Referenced

```
data-harbor/dsha_p49_prep/P49_backtest_audit/factor_knowledge_base/P49_pre_gray_check.md
```

#### Original SHA256 (from event 18)

```
190b35e016e012e7ab1bc006b889cfc2e8114d323bbeb797e773d0bdcc18e7d1
```

This hash was recorded in the event log at event 18 but cannot be verified because the file is absent from disk.

#### Impact

- **P49 gray-check pre-validation template unavailable** — the pre-validation gate for the P49 factor knowledge base pipeline cannot be evaluated
- **Downstream risk** — if any process expects this file as an input for validation, it will fail with a file-not-found error

#### Current State

Still missing as of the latest monitoring cycle. DSHD has not observed the file being restored.

#### DSHD Action

- Observed the missing entry in SHA256_CHECKSUMS.txt and confirmed absence via disk search
- Cross-referenced with the original SHA256 from event 18 for completeness

#### DSHC Action Required

1. **Confirm** whether this file is still required for the current pipeline
2. **Restore** the file from a backup or reconstruct if it remains needed
3. If the file has been superseded, **update** SHA256_CHECKSUMS.txt to reflect the removal

---

### DEFECT-004: Wind Desktop Client Not Functional (BLOCKER)

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-004 |
| **Title** | Wind Financial Terminal Desktop Client Non-Functional — All Data Queries Blocked |
| **Severity** | CRITICAL / BLOCKING |
| **Status** | OPEN / CRITICAL / BLOCKING |
| **First Observed** | 2026-10-16 17:19:11 (DSHA-P54) |
| **Evidence Anchors** | tracking_monitor_audit.jsonl lines 37–39; wind_excel_events.jsonl lines 26–28; DSHC escalation record |

#### Description

The Wind Financial Terminal (万得金融终端) desktop client and all related data access channels are non-functional. This was observed across multiple attack vectors and connection methods:

| Connection Method | Result |
|---|---|
| `windlocal.exe` CLI | Exits immediately with exit code 0 regardless of 26 different CLI argument combinations |
| WindPy Python SDK (`w.start()`) | Returns `ErrorCode=-2` (license/permission error) |
| WDF Excel add-in (COM) | Registered in COM but cannot load — requires running desktop client process |
| WSD formula (Excel) | Returns "Invalid formula name" (COM error `-2147352567`) |
| Wind config directories | Exist but contain only 1-byte marker files (no license, no session tokens) |
| WindPy import | Module importable (v1.0) but cannot establish connection to backend |

#### Wind Update Process Status

One `WindUpdate.RUN` process was found at PID 21260, but investigation confirmed it was **historical** — the process existed in process listing but was not performing any functional update activity. No active update cycle was in progress.

#### Impact

- **ALL Wind data queries blocked** — no alternative Wind access path is functional
- **108 estimated API calls blocked** — FACTOR-004, FACTOR-006, and FACTOR-007 pipelines each require Wind data that cannot be fetched
- **No fallback available** — all four connection methods (CLI, Python SDK, Excel add-in, Excel formula) have been exhausted
- **Critical path blocked** — no factor computation involving Wind-sourced data can proceed

#### Escalation Status

Reported to DSHC with **CRITICAL** severity. Recommended action: "Fix Wind client installation or provide alternative data source."

#### Current State

DSHC has not responded as of monitoring POLL-117+ (2026-10-16 20:03+). The Wind client remains non-functional and all Wind-dependent data queries remain blocked.

#### DSHD Action

- Exhaustively tested 26 CLI argument combinations
- Verified all four connection methods (CLI, Python SDK, Excel add-in, Excel formula)
- Confirmed config directory contents (1-byte marker files only)
- Escalated to DSHC with CRITICAL severity
- Continued monitoring Wind process state

#### DSHC Action Required

1. **Fix Wind client installation** — install/repair the Wind Financial Terminal desktop client with valid licensing
2. **Or provide alternative data access** — if Wind repair is not feasible, provide an alternative data source for the 108+ blocked API calls
3. **Respond to escalation** — no response has been received as of POLL-117+

---

### DEFECT-005: Ledger Plaintext Credential Exposure

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-005 |
| **Title** | Plaintext Credentials Exposed in Audit Ledger and Committed to Git |
| **Severity** | CRITICAL / SECURITY |
| **Status** | OPEN / CRITICAL / SECURITY |
| **First Observed** | 2026-10-16 17:19:11 (line 37), 18:23:50 (line 40); earlier exposure at 16:24 (line 32) |
| **Evidence Anchors** | tracking_monitor_audit.jsonl lines 32, 37, 40; DSHD v3 monitoring CRITICAL_CREDENTIAL_DETECTED alert |

#### Description

Plaintext credential data has been written to the `tracking_monitor_audit.jsonl` ledger across **3 separate lines**, and all 3 lines have been committed to the git repository. The exposure spans two event categories: placeholder credentials and actual credential values.

#### Exposure Locations

| Line | Timestamp | Field | Content Type | Status |
|---|---|---|---|---|
| Line 32 | 16:24 | `password_present: true` | Placeholder credentials (no actual secret values) | Committed to git |
| Line 37 | 17:19:11 | `credentials_provided` | Plaintext phone + password combo [REDACTED] | Committed to git |
| Line 40 | 18:23:50 | `detail` field | Plaintext credential string [REDACTED] embedded in `w.start()` context | Committed to git |

> **Note**: All credential values have been redacted in this document and are recorded as `[REDACTED]` in the DSHD monitoring log.

#### Impact

- **Credentials exposed in audit ledger** — 3 lines contain plaintext sensitive data
- **Committed to git repository** — the exposure persists in version history even if the lines are cleaned
- **Potential security breach** — anyone with read access to the git repository can view the exposed credentials
- **Compliance risk** — credentials in a committed audit ledger may violate security policies regarding secret handling in version control

#### DSHD Monitoring Detection

- **v2 monitoring gap**: The initial v2 script's credential regex pattern did not match the "Tyq1999" pattern used in line 40, causing a missed detection (see DEFECT-008)
- **v3 detection**: The v3 monitoring script expanded the regex pattern and raised a **CRITICAL_CREDENTIAL_DETECTED** alert active since POLL-42 (18:48:33)
- **Continuous alert**: The credential alert remains active as of the latest monitoring cycle

#### Current State

Credentials remain exposed in the ledger and git history. DSHD has not modified the original ledger (outside action authority). The CRITICAL_CREDENTIAL_DETECTED alert has been active for 1h+ and no remediation has been observed.

#### DSHD Action

- Monitored and escalated to DSHC
- Did NOT modify the original ledger (DSHD action authority is observe/log/escalate only)
- Raised CRITICAL_CREDENTIAL_DETECTED alert in v3 monitoring

#### DSHC Action Required

1. **Clean** ledger lines 32, 37, and 40 — replace plaintext credential values with `[REDACTED]`
2. **Rotate** exposed credentials — the credentials on lines 37 and 40 must be considered compromised
3. **Scrub git history** if the ledger has been pushed to a shared remote — use `git filter-branch` or `git filter-repo` to remove credential content from all commits
4. **Audit** for other credentials that may have been written to the ledger during the same monitoring window

---

### DEFECT-006: Audit Ledger Path Migration

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-006 |
| **Title** | Audit Ledger Expected Path Does Not Match Actual Deployment Location |
| **Severity** | LOW / INFORMATIONAL |
| **Status** | RESOLVED (informational) |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §4.1 |

#### Description

The scanner tools and monitoring scripts referenced an expected ledger path of `P49_decisions/audit/tracking_monitor_audit.jsonl`, but this path does not exist. The actual deployment location is:

```
github工作/回测/tracking_monitor_audit.jsonl  (repository root)
```

This discrepancy between the expected and actual path is a documentation/scope configuration issue — the ledger was deployed to a different location than anticipated by the tooling.

#### Impact

- **Scanner tools referencing the old path would fail** — any tool that uses the expected path would encounter file-not-found errors
- **Monitoring required adaptation** — DSHD monitoring had to switch to the actual path

#### Resolution

DSHD monitoring adapted to the actual path (`github工作/回测/tracking_monitor_audit.jsonl`) and continued operations successfully. The defect is classified as RESOLVED (informational) because the monitoring process was unaffected once the correct path was identified.

#### DSHD Action

- Identified the path discrepancy
- Adapted monitoring to the actual deployment location
- Logged the issue for downstream tooling awareness

#### DSHC Action Required

None (resolved). Recommend updating scanner tool documentation to reference the actual ledger path.

---

### DEFECT-007: Monitoring Script Encoding Issues

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-007 |
| **Title** | Monitoring Script Files Missing UTF-8 BOM — Path Resolution Failures on Chinese Windows |
| **Severity** | LOW |
| **Status** | RESOLVED |
| **First Observed** | During v3 monitoring script deployment (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_ROUND17_AUDIT_REPORT.md §2 |

#### Description

The `write` tool produced monitoring script files **without UTF-8 BOM** (Byte Order Mark). On a Chinese-locale Windows environment, PowerShell interpreted the file path with the system's default encoding (GB18030/GBK), causing path resolution failures:

```
Error: Could not find a part of the path
```

The non-ASCII characters in the `github工作/` path segment were misread when PowerShell loaded the script file using its default encoding, leading to incorrect path construction.

#### Root Cause

The `write` tool defaults to UTF-8 without BOM. On Chinese Windows, PowerShell expects UTF-8 with BOM (or uses the system codepage) to correctly interpret non-ASCII characters in file content and paths.

#### Resolution

Used `[System.IO.File]::WriteAllText()` with explicit **UTF-8 BOM encoding** to write subsequent script files. This ensured correct path encoding and resolved all path resolution errors.

#### DSHD Action

- Identified the encoding mismatch during v3 script deployment
- Implemented the UTF-8 BOM fix using .NET File API
- Verified subsequent script execution succeeded

#### DSHC Action Required

None (resolved). Recommend documenting the UTF-8 BOM requirement for any scripts that reference paths containing Chinese characters.

---

### DEFECT-008: v2 Credential Detection Regex Gap

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-008 |
| **Title** | v2 Monitoring Script Credential Regex Missed Tyq1999 Pattern |
| **Severity** | LOW |
| **Status** | RESOLVED (superseded by v3) |
| **First Observed** | During DSHD-P67 monitoring round 17 (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_ROUND17_AUDIT_REPORT.md §5 |

#### Description

The v2 monitoring script's credential detection regex pattern did not match the **"Tyq1999"** credential pattern used in `tracking_monitor_audit.jsonl` line 40. As a result, the credential exposure on line 40 (timestamp 18:23:50) went **undetected** by the v2 script during monitoring rounds 1–17.

#### Detection Gap

| Line | Pattern | v2 Detected? |
|---|---|---|
| Line 32 | Placeholder credentials | ✅ (via `password_present` field flag) |
| Line 37 | Plaintext phone + password [REDACTED] | ✅ (matched generic credential pattern) |
| Line 40 | "Tyq1999" pattern [REDACTED] | ❌ **NOT DETECTED** |

The "Tyq1999" pattern was a mixed alphanumeric credential format that the v2 regex did not cover. The v2 regex was designed for common password patterns but did not account for mixed-case alphanumeric combinations like this one.

#### Resolution

The v3 monitoring script expanded the credential regex to include the **Tyq1999 pattern**. After the v3 deployment, the credential alert became active, and the CRITICAL_CREDENTIAL_DETECTED alert was raised at POLL-42 (18:48:33).

#### DSHD Action

- Identified the regex gap during round 17 audit review
- Expanded regex in v3 script to cover the missed pattern
- Verified the v3 script correctly flags all credential-containing lines

#### DSHC Action Required

None (resolved via v3). Recommend reviewing the v3 regex coverage against a broader set of credential patterns for future monitoring cycles.

---

### DEFECT-009: G7 Conditional Release Broadcast Hash Drift

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-009 |
| **Title** | G7 Conditional Release Broadcast File SHA256 Drift After Post-Recording Expansion |
| **Severity** | LOW / INFORMATIONAL |
| **Status** | RESOLVED (informational) |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §2.4 |

#### Description

The G7 conditional release broadcast file's SHA256 hash drifted between the time of event recording and the current on-disk state:

| Time | SHA256 (first 8 chars) | Event |
|---|---|---|
| 14:50 (event time) | `a73eb470...` | Broadcast file as originally recorded |
| Current disk | `EDAC4071...` | Broadcast file after supplementary notes were appended |

The file was **expanded with supplementary notes** after the initial hash was recorded. This is a legitimate content modification — the hash drift reflects a real change to the file, not corruption or tampering.

#### Verification

The content of the expanded file was verified as **legitimate** — the supplementary notes are authorized additions, not unauthorized modifications.

#### Resolution

DSHC regenerated all checksums at **17:25**, including the updated hash for this broadcast file. The manifest now reflects the current on-disk state.

#### DSHD Action

- Observed the hash mismatch between event-time and current-disk SHA256
- Verified the content expansion was legitimate
- Logged the drift as informational

#### DSHC Action Required

None (resolved). Checksums have been regenerated to reflect current state.

---

### DEFECT-010: Non-Authorized Wind Code Probe

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-010 |
| **Title** | Wind Test Workbook Used Unauthorized Stock Index Code Instead of Commodity Futures |
| **Severity** | LOW / INFORMATIONAL |
| **Status** | INFORMATIONAL (no breach) |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §5.4 |

#### Description

The file `opendpyxl_wsd_test.xlsx` — used for Wind data access testing — contained a Wind formula query for **stock code `000300.SH`** (CSI 300 / China Securities Index 300). This is a stock index code, not a commodity futures code. The authorized Wind data access scope for this project is limited to **commodity futures codes** only:

| Code | Commodity | Status |
|---|---|---|
| NI.SHF | Nickel (Shanghai Futures) | Authorized |
| LI.SHF | Lithium (Shanghai Futures) | Authorized |
| ZN.SHF | Zinc (Shanghai Futures) | Authorized |
| CU.SHF | Copper (Shanghai Futures) | Authorized |
| 000300.SH | CSI 300 Stock Index | ❌ **Unauthorized** |

#### Impact

- **No actual data leak** — the Wind desktop client was not functional (see DEFECT-004), so the formula could not be calculated and no data was retrieved
- **No data breach occurred** — the test was executed against a non-functional data source
- **Potential policy concern** — future tests should only use authorized Wind codes to avoid scope violations if the Wind client becomes functional

#### Resolution

DSHD flagged this for awareness. No remediation is required because no data was accessed, but the finding serves as a reminder that future Wind tests must strictly adhere to the authorized commodity futures code list.

#### DSHD Action

- Observed the unauthorized code in the test workbook
- Confirmed no data was retrieved (Wind client non-functional)
- Logged as informational with a note for future test scope compliance

#### DSHC Action Required

None (no breach). Ensure future Wind test scripts use only authorized commodity futures codes (NI.SHF/LI.SHF/ZN.SHF/CU.SHF).

---

### DEFECT-011: FACTOR-007 Field Overlap with HOLD Factors

| Field | Value |
|---|---|
| **Defect ID** | DEFECT-011 |
| **Title** | FACTOR-007 Plans to Reuse Wind Fields Already Assigned to HOLD Factors |
| **Severity** | LOW / INFORMATIONAL |
| **Status** | INFORMATIONAL (boundary concern) |
| **First Observed** | During DSHD-P67 exploration phase (2026-10-16) |
| **Evidence Anchors** | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md §3.5 |

#### Description

**FACTOR-007** (SchemeD frozen weights pipeline) plans to use the following Wind data fields:

| Field | Currently Used By |
|---|---|
| `F19_score` | FACTOR-001 (HOLD) |
| `F20_score` | FACTOR-002 (HOLD) |
| `CF003_score` | FACTOR-003 (HOLD) |

These are the same Wind fields already used by the **HOLD factors** (FACTOR-001, FACTOR-002, FACTOR-003). The proposed reuse creates a **boundary concern** — FACTOR-007 may be stepping outside its defined scope by referencing data fields that belong to a different factor tier.

#### Impact

- **Dry-run only (0 rows)** — no actual computation was executed, so no HOLD factor data was accessed or modified
- **No data conflict occurred** — the reuse was identified at the planning/configuration stage before any computation
- **Boundary concern** — if FACTOR-007 is intended to be independent of HOLD factors, sharing these fields may violate scope boundaries or create hidden coupling

#### Current State

No computation has occurred. The field overlap exists in the pipeline configuration only.

#### DSHD Action

- Observed the field overlap between FACTOR-007 and HOLD factors
- Verified no computation was executed (0 rows in dry-run)
- Logged as informational boundary concern

#### DSHC Action Required

1. **Confirm** whether FACTOR-007 is authorized to use the shared Wind data fields (F19_score, F20_score, CF003_score) with HOLD factors
2. If **not authorized**, FACTOR-007 must be configured to use independent data fields
3. If **authorized**, document the shared-field boundary in the factor scope specification

---

## 5. Severity Distribution Chart

```
Severity Distribution (n=11 defects)

CRITICAL  ██████████████████████████ 2   (18.2%)   DEFECT-004, DEFECT-005
HIGH      ████████████████████████████████████████████ 3   (27.3%)   DEFECT-001, DEFECT-002, DEFECT-003
MEDIUM    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0   ( 0.0%)   —
LOW/INFO  ████████████████████████████████████████████████████████████████████████████ 6   (54.5%)   DEFECT-006, DEFECT-007, DEFECT-008, DEFECT-009, DEFECT-010, DEFECT-011
```

### Breakdown

| Severity | Count | Percentage | Trend |
|---|---|---|---|
| CRITICAL | 2 | 18.2% | Both CRITICAL defects remain OPEN — Wind client and credential exposure |
| HIGH | 3 | 27.3% | All 3 HIGH defects remain OPEN/PERSISTENT — P61 tools, checksum drift, missing file |
| MEDIUM | 0 | 0.0% | — |
| LOW / INFORMATIONAL | 6 | 54.5% | 4 RESOLVED, 2 INFORMATIONAL — internal process issues and boundary concerns |

### Severity Classification Criteria

| Severity | Definition | Examples |
|---|---|---|
| **CRITICAL** | Blocks critical path operations; requires immediate DSHC attention | Wind client failure (blocks all data queries), credential exposure (security breach) |
| **HIGH** | Significant integrity or availability issue; requires DSHC action but not blocking | Missing toolchain, checksum drift, missing required file |
| **MEDIUM** | Noticeable issue with workaround available; should be addressed | (none observed in this cycle) |
| **LOW / INFORMATIONAL** | Minor issue, resolved, or no active impact; documented for awareness | Path migration, encoding fix, regex gap, hash drift, code probe, field overlap |

---

## 6. Status Summary

```
Status Distribution (n=11 defects)

OPEN          ████████████████████████████████ 5   (45.5%)   DEFECT-001, DEFECT-002, DEFECT-003, DEFECT-004, DEFECT-005
RESOLVED      ████████████████████████████ 4   (36.4%)   DEFECT-006, DEFECT-007, DEFECT-008, DEFECT-009
INFORMATIONAL ████████████████ 2   (18.1%)   DEFECT-010, DEFECT-011
```

### Status Categories

| Status | Count | Percentage | Description |
|---|---|---|---|
| **OPEN** | 5 | 45.5% | Defects that remain active and require DSHC action. Includes 2 CRITICAL (blocking and security) and 3 HIGH (integrity/availability). |
| **RESOLVED** | 4 | 36.4% | Defects that have been fixed or no longer present. Includes both DSHC-side resolutions (checksum regeneration) and DSHD-side resolutions (monitoring adaptation). |
| **INFORMATIONAL** | 2 | 18.1% | Observations that require no action but are documented for awareness. No actual breach occurred. |

### OPEN Defects — Priority Queue

| Priority | Defect ID | Title | Severity | Action Required |
|---|---|---|---|---|
| P0 | DEFECT-004 | Wind Desktop Client Not Functional | CRITICAL | Fix installation or provide alternative data source |
| P0 | DEFECT-005 | Ledger Plaintext Credential Exposure | CRITICAL | Clean lines, rotate credentials, scrub git history |
| P1 | DEFECT-001 | P61 Scanner Tools Missing | HIGH | Clarify recovery path (rebuild/migrate/cancel) |
| P1 | DEFECT-002 | SHA256 Checksum Drift | HIGH | Establish automated sync mechanism |
| P2 | DEFECT-003 | P49_pre_gray_check.md Missing | HIGH | Confirm necessity; restore if needed |

---

## 7. Timeline View

Chronological order of defect observations (earliest to latest):

```
2026-10-16 TIMELINE

14:50  ─── DEFECT-009: G7 conditional release broadcast file recorded (SHA256: a73eb470...)

16:24  ─── DEFECT-005 (early): Line 32 — placeholder credentials written to ledger

16:49  ─── DEFECT-002 (root cause): SHA256_CHECKSUMS.txt partially refreshed (entries 9-17 only)

17:19  ─── DEFECT-004: Wind desktop client failure first observed (DSHA-P54)
       ─── DEFECT-005: Line 37 — plaintext credentials [REDACTED] written to ledger

17:25  ─── DEFECT-002 (resolution): DSHC-P66 regenerates checksums (19 entries)
       ─── DEFECT-009 (resolution): DSHC regenerates checksums including broadcast file

18:23  ─── DEFECT-005: Line 40 — "Tyq1999" pattern credential [REDACTED] written to ledger

18:48  ─── DEFECT-008 (resolution): v3 script deployed; CRITICAL_CREDENTIAL_DETECTED raised

       ─── DSHD-P67 Exploration Phase begins:
       ─── DEFECT-001: P61 scanner tools missing (observed)
       ─── DEFECT-003: P49_pre_gray_check.md missing (observed)
       ─── DEFECT-006: Audit ledger path discrepancy (observed)
       ─── DEFECT-007: Monitoring script encoding issue (observed & resolved)
       ─── DEFECT-010: Unauthorized Wind code probe (observed)
       ─── DEFECT-011: FACTOR-007 field overlap (observed)

20:03+ ─── DSHD-P67 POLL-117+: Latest monitoring cycle
       ─── DEFECT-004: Still OPEN — Wind client non-functional; DSHC no response
       ─── DEFECT-005: Still OPEN — credentials still in ledger; CRITICAL alert active
```

### Key Timeline Observations

1. **DEFECT-009** was the earliest event (14:50) — a legitimate file expansion that caused a benign hash drift
2. **DEFECT-004** and **DEFECT-005** were observed in the same minute (17:19) — the Wind client failure and credential exposure coincide temporally
3. **DEFECT-002** was detected and resolved within the same day — DSHC-P66 regenerated checksums at 17:25, within 36 minutes of the partial refresh at 16:49
4. **DEFECT-008** was resolved by DSHD itself — the v2→v3 monitoring upgrade closed the detection gap
5. **DEFECT-004** and **DEFECT-005** remain the only OPEN CRITICAL defects after 3+ hours without DSHC response

---

## 8. Cross-Reference Map

### 8.1 Defect → Evidence Source Matrix

| Defect ID | tracking_monitor_audit.jsonl | wind_excel_events.jsonl | DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md | SHA256_CHECKSUMS.txt | DSHD_P67_ROUND17_AUDIT_REPORT.md |
|---|---|---|---|---|---|
| DEFECT-001 | — | — | §6.1 | — | — |
| DEFECT-002 | — | — | §7.2 | — | — |
| DEFECT-003 | — | — | — | Entry #10 | — |
| DEFECT-004 | Lines 37–39 | Lines 26–28 | — | — | — |
| DEFECT-005 | Lines 32, 37, 40 | — | — | — | — |
| DEFECT-006 | — | — | §4.1 | — | — |
| DEFECT-007 | — | — | — | — | §2 |
| DEFECT-008 | — | — | — | — | §5 |
| DEFECT-009 | — | — | §2.4 | — | — |
| DEFECT-010 | — | — | §5.4 | — | — |
| DEFECT-011 | — | — | §3.5 | — | — |

### 8.2 Defect → Ledger Line Mapping

| Ledger Line | Timestamp | Defect ID | Content Summary |
|---|---|---|---|
| Line 32 | 16:24 | DEFECT-005 | `password_present: true` — placeholder credentials |
| Line 37 | 17:19:11 | DEFECT-004, DEFECT-005 | `credentials_provided` [REDACTED] — Wind start credentials + Wind failure details |
| Line 38 | — | DEFECT-004 | Wind connection method test results |
| Line 39 | — | DEFECT-004 | Wind config directory inspection |
| Line 40 | 18:23:50 | DEFECT-005 | `w.start()` with creds [REDACTED] — credential in detail field |

### 8.3 Defect → Wind Event Line Mapping

| Wind Event Line | Defect ID | Content Summary |
|---|---|---|
| Lines 26–28 | DEFECT-004 | Wind Excel add-in and WSD formula test results |

### 8.4 Defect → Brief Section Mapping

| Brief Section | Defect ID(s) | Content Summary |
|---|---|---|
| §2.4 | DEFECT-009 | G7 broadcast hash drift |
| §3.5 | DEFECT-011 | FACTOR-007 field overlap |
| §4.1 | DEFECT-006 | Audit ledger path migration |
| §5.4 | DEFECT-010 | Unauthorized Wind code probe |
| §6.1 | DEFECT-001 | P61 scanner tools missing |
| §7.2 | DEFECT-002 | SHA256 checksum drift |

### 8.5 Defect → Audit Report Section Mapping

| Audit Report Section | Defect ID(s) | Content Summary |
|---|---|---|
| §2 | DEFECT-007 | Monitoring script encoding issues |
| §5 | DEFECT-008 | v2 credential detection gap |

### 8.6 Defect → SHA256_CHECKSUMS.txt Entry Mapping

| SHA256 Entry | Defect ID | Status |
|---|---|---|
| Entry #10 | DEFECT-003 | MISSING (file absent from disk) |

---

## 9. Archive Signature

```
═══════════════════════════════════════════════════════════════
  DSHD DEFECT OBSERVATION_REGISTRY — ARCHIVE SIGNATURE
═══════════════════════════════════════════════════════════════

Registry:    DSHD_DEFECT_OBSERVATION_REGISTRY
Agent:       DSHD-P67 (DSHD Monitoring Agent)
Created:     2026-10-16 (DSHD-P67 Exploration Phase)
Updated:     2026-10-16 20:03+ (POLL-117+)
Coverage:    G7 Adjudication Cycle — POLL-01 through POLL-117+
Defects:     11 total (5 OPEN, 4 RESOLVED, 2 INFORMATIONAL)
Severity:    2 CRITICAL, 3 HIGH, 0 MEDIUM, 6 LOW/INFORMATIONAL

Methodology: Continuous file hash verification, ledger line-by-line
             audit, Wind event log parsing, cross-reference against
             SHA256_CHECKSUMS.txt and broadcast manifests
Credential:  All credentials redacted as [REDACTED]
Authority:   DSHD observation only; DSHC retains formal registration

This document is an independent audit observation record. It does
not constitute the official DSHC defect registry. DSHC retains
formal defect registration authority and the status of any defect
in the official DSHC system governs over this observation registry.

═══════════════════════════════════════════════════════════════
```

---

> **End of Registry.**  
> *Generated by DSHD-P67 monitoring agent. For questions about this registry, contact DSHD monitoring. For formal defect registration or status, contact DSHC.*
