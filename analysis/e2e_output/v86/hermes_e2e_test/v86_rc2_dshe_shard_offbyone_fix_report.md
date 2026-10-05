# DSHE V86-RC2 L2 Evidence Shard Off-By-One Fix Report

**Work Order:** DSHE_V86_RC2_L2_SHARD_BUGFIX_PROD_ADAPT  
**Sub-Task:** T3.1 — P0 Off-By-One Defect Fix  
**Branch:** feature/v85-chart-template  
**HEAD:** b259999  
**Date:** 2026-10-15  
**Severity:** P0 (Critical)  

---

## 1. Root Cause Analysis

### 1.1 Bug Location

The P0 defect is located in `ShardedJSONReader.__init__` in `l2_evidence_package_check_v3.py` (line 430):

```python
self.shard_count = max(1, self.file_size // self.shard_size + 1)
```

### 1.2 Root Cause

The formula uses **floor division + 1** (`file_size // shard_size + 1`) instead of **ceiling division** (`ceil(file_size / shard_size)`). These are mathematically equivalent **except** when `file_size` is an exact multiple of `shard_size`.

The intent of the formula was: "compute how many shards are needed to cover `file_size` bytes with `shard_size`-byte chunks." The correct mathematical formula for this is ceiling division:

```
shard_count = ceil(file_size / shard_size)
```

In Python, ceiling division for positive integers can be expressed as:

```python
shard_count = -(-file_size // shard_size)
```

This works because Python's `//` operator performs floor division (truncates toward negative infinity). Negating the operands and then negating the result converts floor division into ceiling division.

### 1.3 Why the Old Formula Was Wrong

The old formula `file_size // shard_size + 1` always adds 1 shard beyond what's needed when `file_size` is an exact multiple of `shard_size`. This is because:

- `file_size // shard_size` gives the number of **complete** shards
- `+ 1` adds a **partial** shard

But when `file_size` is exactly divisible by `shard_size`, there is **no partial shard** — all data fits exactly into complete shards.

**Example:**
- `file_size = 4194304` (4 MB), `shard_size = 4194304` (4 MB)
- `4194304 // 4194304 = 1` → complete shards
- `+ 1 = 2` → but there is NO second shard! All data fits in 1 shard.

### 1.4 Impact Assessment

The bug causes **one extra shard to be counted** whenever `file_size` is an exact multiple of `shard_size`. This has the following impacts:

| Impact Area | Severity | Description |
|---|---|---|
| **Memory estimation** | MEDIUM | Overestimates memory needed by 1 shard worth |
| **Progress reporting** | LOW | Reports incorrect progress (e.g., "shard 1/2" when only 1 exists) |
| **Shard boundary calculations** | MEDIUM | Incorrect shard offsets/boundaries for exact-multiple files |
| **Data integrity** | LOW | No data loss, just over-counting |
| **Performance** | LOW | Minor overhead from unnecessary shard processing logic |

The P0 classification is based on the potential for **silent data corruption** in scenarios where shard-based processing uses the shard_count to determine read/write boundaries.

---

## 2. Old Formula vs New Formula Comparison

### 2.1 Formula Definitions

| Property | Old Formula (V3) | New Formula (V4) |
|---|---|---|
| **Expression** | `max(1, file_size // shard_size + 1)` | `max(1, -(-file_size // shard_size))` |
| **Method** | Floor division + 1 | Ceiling division |
| **Correct when file_size is multiple of shard_size?** | ❌ NO | ✅ YES |
| **Correct when file_size is NOT a multiple of shard_size?** | ✅ YES | ✅ YES |
| **Correct for empty file (0 bytes)?** | ✅ YES | ✅ YES |

### 2.2 Mathematical Equivalence Proof

For any positive integers `a` and `b`:

```
ceil(a / b) = -(-a // b) = a // b + (1 if a % b > 0 else 0)
```

The old formula `a // b + 1` differs from `ceil(a / b)` only when `a % b == 0`:

```
When a % b > 0:
  old = a // b + 1 = ceil(a / b)  ✅ CORRECT

When a % b == 0:
  old = a // b + 1 = ceil(a / b) + 1  ❌ WRONG (off by one)
```

---

## 3. Boundary Test Cases

### Test Case 1: `file_size == shard_size` (The P0 Bug Case)

| Parameter | Value |
|---|---|
| `file_size` | 4,194,304 (4 MB) |
| `shard_size` | 4,194,304 (4 MB) |
| **Old Formula (V3)** | `max(1, 4194304 // 4194304 + 1)` = `max(1, 1 + 1)` = **2** ❌ WRONG |
| **New Formula (V4)** | `max(1, -(-4194304 // 4194304))` = `max(1, 1)` = **1** ✅ CORRECT |

**Explanation:** A 4MB file with 4MB shards needs exactly 1 shard. The old formula incorrectly reported 2 shards, which would cause downstream shard boundary calculations to be off by one full shard.

---

### Test Case 2: `file_size == shard_size + 1` (Not affected)

| Parameter | Value |
|---|---|
| `file_size` | 4,194,305 (4 MB + 1 byte) |
| `shard_size` | 4,194,304 (4 MB) |
| **Old Formula (V3)** | `max(1, 4194305 // 4194304 + 1)` = `max(1, 1 + 1)` = **2** ✅ CORRECT |
| **New Formula (V4)** | `max(1, -(-4194305 // 4194304))` = `max(1, 2)` = **2** ✅ CORRECT |

**Explanation:** A 4MB+1byte file with 4MB shards needs 2 shards (one complete + one partial). Both formulas correctly report 2 shards.

---

### Test Case 3: Empty File (`file_size == 0`)

| Parameter | Value |
|---|---|
| `file_size` | 0 |
| `shard_size` | 4,194,304 (4 MB) |
| **Old Formula (V3)** | `max(1, 0 // 4194304 + 1)` = `max(1, 0 + 1)` = **1** ✅ CORRECT |
| **New Formula (V4)** | `max(1, -(-0 // 4194304))` = `max(1, 0)` = **1** ✅ CORRECT |

**Explanation:** An empty file should have at least 1 shard (as defined by the `max(1, ...)` guard). Both formulas correctly report 1 shard. The `max(1, ...)` ensures a minimum of 1 shard regardless of file size.

---

### Additional Boundary Cases

| # | `file_size` | `shard_size` | Old (V3) | New (V4) | Correct? |
|---|---|---|---|---|---|
| 1 | 0 | 4096 | 1 | 1 | ✅ Both correct |
| 2 | 1 | 4096 | 1 | 1 | ✅ Both correct |
| 3 | 4095 | 4096 | 1 | 1 | ✅ Both correct |
| 4 | **4096** | **4096** | **2** | **1** | ❌ Old WRONG, ✅ New correct |
| 5 | 4097 | 4096 | 2 | 2 | ✅ Both correct |
| 6 | **8192** | **4096** | **3** | **2** | ❌ Old WRONG, ✅ New correct |
| 7 | 8193 | 4096 | 3 | 3 | ✅ Both correct |
| 8 | **12288** | **4096** | **4** | **3** | ❌ Old WRONG, ✅ New correct |

---

## 4. Before/After Behavior Comparison

### 4.1 Before Fix (V3 — Buggy)

```python
# V3 ShardedJSONReader.__init__
self.shard_count = max(1, self.file_size // self.shard_size + 1)
```

| Scenario | shard_count | Correct? | Downstream Impact |
|---|---|---|---|
| 0 bytes / 4MB shard | 1 | ✅ | None |
| 1 byte / 4MB shard | 1 | ✅ | None |
| 4MB-1 byte / 4MB shard | 1 | ✅ | None |
| **4MB / 4MB shard** | **2** | ❌ | Memory over-estimate, wrong progress, wrong boundaries |
| 4MB+1 byte / 4MB shard | 2 | ✅ | None |
| **8MB / 4MB shard** | **3** | ❌ | Same as above, amplified |
| **16MB / 4MB shard** | **5** | ❌ | Same as above, further amplified |

### 4.2 After Fix (V4 — Correct)

```python
# V4 ShardedJSONReader.__init__
self.shard_count = max(1, -(-self.file_size // self.shard_size))
```

| Scenario | shard_count | Correct? | Downstream Impact |
|---|---|---|---|
| 0 bytes / 4MB shard | 1 | ✅ | None |
| 1 byte / 4MB shard | 1 | ✅ | None |
| 4MB-1 byte / 4MB shard | 1 | ✅ | None |
| **4MB / 4MB shard** | **1** | ✅ | Correct behavior |
| 4MB+1 byte / 4MB shard | 2 | ✅ | None |
| **8MB / 4MB shard** | **2** | ✅ | Correct behavior |
| **16MB / 4MB shard** | **4** | ✅ | Correct behavior |

---

## 5. Fix Implementation

### 5.1 Code Change

**File:** `l2_evidence_package_check_v4.py`  
**Class:** `ShardedJSONReader.__init__`

```python
# BEFORE (V3 — Buggy):
self.shard_count = max(1, self.file_size // self.shard_size + 1)

# AFTER (V4 — Fixed):
self.shard_count = max(1, -(-self.file_size // self.shard_size))
```

### 5.2 Explanation

The fix uses Python's integer ceiling division idiom:

```python
ceil(a / b) = -(-a // b)
```

This is the standard Python idiom for ceiling division with integers. It works because:
1. `-a // b` performs floor division on `-a` (e.g., `-4 // 2 = -2`)
2. Negating the result converts floor to ceiling: `-(-2) = 2`

### 5.3 Added Utility Methods

Two new static methods were added to `ShardedJSONReader` for testing and regression prevention:

```python
@staticmethod
def compute_shard_count(file_size, shard_size):
    """Correctly compute shard count using ceiling division."""
    if shard_size <= 0:
        raise ValueError("shard_size must be > 0")
    if file_size <= 0:
        return 1
    return max(1, -(-file_size // shard_size))

@staticmethod
def verify_shard_count(file_size, shard_size):
    """Compare old (V3) and new (V4) formulas for regression testing."""
    old_count = max(1, file_size // shard_size + 1)
    new_count = max(1, -(-file_size // shard_size))
    return {
        "file_size": file_size,
        "shard_size": shard_size,
        "old_formula_v3": old_count,
        "new_formula_v4": new_count,
        "match": old_count == new_count,
        "off_by_one_bug": old_count != new_count,
    }
```

---

## 6. Test Results

All 39 exception handling tests passed after the fix, including 7 dedicated shard_count tests:

```
[V4 TEST] PASS: shard_count[file==shard] old=2 (BUG), new=1, expected=1
[V4 TEST] PASS: shard_count[file==shard+1] old=2, new=2, expected=2 (both correct)
[V4 TEST] PASS: shard_count[empty_file] old=1, new=1, expected=1
[V4 TEST] PASS: shard_count[file==2*shard] old=3 (BUG), new=2, expected=2
[V4 TEST] PASS: shard_count[single_byte] old=1, new=1, expected=1
[V4 TEST] PASS: compute_shard_count[all] all 6 boundary values correct
[V4 TEST] PASS: verify_shard_count[file==shard] old=2, new=1, bug=True
```

Additional boundary cases verified:
- `boundary_empty_file`: shard_count=1 ✅
- `boundary_single_byte`: shard_count=1 ✅
- `boundary_just_below`: shard_count=1 ✅
- `boundary_exact_match`: shard_count=1 ✅
- `boundary_just_above`: shard_count=2 ✅
- `boundary_exact_double`: shard_count=2 ✅
- `boundary_just_above_double`: shard_count=3 ✅
- `boundary_exact_triple`: shard_count=3 ✅
- `boundary_large_file`: shard_count=2560 ✅

---

## 7. Verification Command

```bash
# Run the built-in exception handling test suite
python l2_evidence_package_check_v4.py --exception-handling-test

# Expected output: All 39 tests PASSED
```

---

## 8. Files Changed

| File | Action | Lines Changed |
|---|---|---|
| `l2_evidence_package_check_v3.py` | **UNCHANGED** (NO_MODIFY_V85=TRUE) | — |
| `l2_evidence_package_check_v4.py` | **NEW** | ~1600 lines (V4 based on V3 + enhancements) |

---

## 9. Sign-off

| Role | Status | Date |
|---|---|---|
| Bug Reporter | Identified P0 | 2026-10-15 |
| Fix Author | V4 implementation complete | 2026-10-15 |
| Test Runner | 39/39 tests PASS | 2026-10-15 |
