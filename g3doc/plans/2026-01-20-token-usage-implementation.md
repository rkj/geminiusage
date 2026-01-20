# Gemini Token Usage Calculator Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use executing-plans or subagent-driven-development to implement this plan task-by-task.

**Goal:** Create a standalone Python script to calculate token usage and costs from Gemini CLI session histories.

**Architecture:** A single Python script that uses `pathlib` for recursive file searching, `json` for data extraction, and `collections.defaultdict` for per-day/per-model aggregation.

**Tech Stack:** Python 3 (standard library only for maximum portability).

---

### Task 1: Project Setup and Base Script

**Files:**
- Create: `scripts/token-usage.py`

**Step 1: Create the scripts directory**
Run: `mkdir -p scripts`

**Step 2: Initialize the script with imports and pricing defaults**
```python
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DEFAULT_PRICING = {
    "gemini-3-flash-preview": {
        "input": 0.10,
        "cached": 0.05,
        "output": 0.40
    }
}
```

---

### Task 2: Implement File Discovery and Aggregation

**Files:**
- Modify: `scripts/token-usage.py`

**Step 1: Implement the `aggregate_usage()` function**
- Scan `~/.gemini/tmp/*/chats/session-*.json`.
- Parse messages and sum tokens.
- Handle missing `tokens` fields gracefully.

```python
def aggregate_usage(base_path):
    stats = defaultdict(lambda: defaultdict(lambda: {"sessions": 0, "input": 0, "cached": 0, "output": 0}))
    # ... logic to scan and parse ...
    return stats
```

---

### Task 3: Implement Pricing and Calculation

**Files:**
- Modify: `scripts/token-usage.py`

**Step 1: Implement cost calculation logic**
- Load `pricing.json` if it exists.
- Apply rates per model.

---

### Task 4: Implement Tabular Output

**Files:**
- Modify: `scripts/token-usage.py`

**Step 1: Format the data into a table**
- Use f-strings for alignment.
- Sort by date and then model.

---

### Task 5: Testing and Verification

**Files:**
- Create: `scripts/token-usage_test.py`

**Step 1: Write a unit test for the aggregator**
- Mock the file system or use temporary files.
- Verify totals for a known sample session.

**Step 2: Run the test**
Run: `python3 scripts/token-usage_test.py`

**Step 3: Run the final script on live data**
Run: `python3 scripts/token-usage.py`
