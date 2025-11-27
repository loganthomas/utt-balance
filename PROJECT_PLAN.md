# UTT Plugin Project Plan

## Project Overview

Convert the standalone `check_time` utility into a proper UTT plugin that integrates natively with the UTT time tracking library.

---

## Naming Recommendations

Your plugin needs a good name for PyPI distribution. Here are my recommendations:

| Name | Pros | Cons |
|------|------|------|
| **`utt-balance`** ⭐ | Short, memorable, describes the "balance" of worked vs remaining time, resonates with "work-life balance" concept | None significant |
| `utt-check` | Simple, matches your original idea | Too generic, doesn't convey what it checks |
| `utt-quota` | Clear purpose (checking work quota) | Less intuitive |
| `utt-tally` | Conveys summing up time | Less common word |
| `utt-status` | Shows current status | Might conflict with git-style thinking |

### **Recommended: `utt-balance`**

Reasons:
1. Short and memorable (11 characters)
2. Follows the `utt-*` naming convention for discoverability
3. Describes functionality: checking the "balance" of time worked vs remaining
4. Professional and intuitive
5. Will install as: `pip install utt-balance`
6. Command will be: `utt balance`

---

## Current State Analysis

### Your Existing Utility (`check_time`)

**What it does:**
- Calculates worked time for today and since Sunday (weekly)
- Shows remaining time to reach daily (8h) and weekly (40h) targets
- Displays a Rich-formatted table with color coding:
  - Yellow: exactly at target
  - Red: over target or negative remaining

**Current approach (problematic):**
```python
# Shells out to utt CLI and parses text output
utt_out = subprocess.check_output(["utt report --from sunday ..."], shell=True)
worked_str = re.findall(r"Working: (\d+h\d+)", utt_str)[0]
```

**Problems with current approach:**
1. Depends on text output format (fragile)
2. Spawns subprocess (slow, inefficient)
3. Not integrated with UTT ecosystem
4. Can't leverage UTT's configuration or components

---

## UTT Plugin System Analysis

### How UTT Plugins Work

1. **Namespace Packages**: Plugins are Python namespace packages under `utt.plugins`
2. **Empty `__init__.py`**: Both `utt/` and `utt/plugins/` need empty `__init__.py` files
3. **Registration**: Commands/components registered via `_v1.register_command()` and `_v1.register_component()`

### Available Injectable Components (from `utt.api._v1`)

| Component | Description |
|-----------|-------------|
| `Now` | Current datetime |
| `Output` | Output stream (for printing) |
| `Entries` | List of time entries from the log |
| `Activities` | List of activities (derived from entries) |
| `ReportModel` | Full report model with summary, details, etc. |
| `Entry` | Single entry data structure |
| `Activity` | Single activity with start/end/duration/type |

### Activity Types
- `Activity.Type.WORK` (0) - Working activities
- `Activity.Type.BREAK` (1) - Break activities (suffix `**`)
- `Activity.Type.IGNORED` (2) - Ignored activities (suffix `***`)

---

## Implementation Plan

### Phase 1: Project Setup

- [ ] **1.1** Rename repository from `new-repo` to `utt-balance`
- [ ] **1.2** Create proper Python package structure:
  ```
  utt-balance/
  ├── pyproject.toml          # Modern Python packaging (Poetry or setuptools)
  ├── README.md               # Documentation
  ├── LICENSE                 # License file
  └── src/
      └── utt_balance/        # Package source
          ├── __init__.py     # Package init with version
          └── utt/            # Namespace package (no __init__.py or empty)
              └── plugins/    # Namespace package (no __init__.py or empty)
                  └── balance_command.py  # The actual plugin
  ```
- [ ] **1.3** Configure `pyproject.toml` for PyPI publishing

### Phase 2: Core Plugin Development

- [ ] **2.1** Create `BalanceHandler` class that uses UTT's injectable components:
  - Inject `Activities` to get activity data directly
  - Inject `Now` for current time
  - Inject `Output` for printing
- [ ] **2.2** Implement time calculation logic:
  - Calculate working time from activities (filter by `Activity.Type.WORK`)
  - Support daily and weekly targets
  - Calculate remaining time
- [ ] **2.3** Create the `balance` command with argument parsing:
  - `--daily-hours` (default: 8)
  - `--weekly-hours` (default: 40)
  - `--week-start` (default: sunday)
- [ ] **2.4** Register command with UTT

### Phase 3: Output & Display

- [ ] **3.1** Keep Rich table output (matches your current design)
- [ ] **3.2** Implement color-coded formatting:
  - Green: under target
  - Yellow: exactly at target
  - Red: over target or negative remaining
- [ ] **3.3** Add optional plain-text output mode

### Phase 4: Testing

- [ ] **4.1** Unit tests for time calculations
- [ ] **4.2** Integration tests with mock UTT data
- [ ] **4.3** Manual testing with real UTT installation

### Phase 5: Documentation & Publishing

- [ ] **5.1** Write comprehensive README.md
- [ ] **5.2** Add usage examples
- [ ] **5.3** Configure GitHub Actions for CI/CD
- [ ] **5.4** Publish to PyPI

---

## Technical Design

### New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         UTT Core                            │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Entries │  │Activities│  │   Now   │  │    Output    │  │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └──────┬───────┘  │
│       │            │             │               │          │
└───────┼────────────┼─────────────┼───────────────┼──────────┘
        │            │             │               │
        ▼            ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    utt-balance Plugin                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   BalanceHandler                      │  │
│  │  - Receives Activities, Now, Output via injection    │  │
│  │  - Calculates daily/weekly worked time               │  │
│  │  - Computes remaining time against targets           │  │
│  │  - Renders Rich table output                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Handler Implementation (Conceptual)

```python
from utt.api import _v1
from datetime import timedelta

class BalanceHandler:
    def __init__(
        self,
        activities: _v1.Activities,
        now: _v1.Now,
        output: _v1.Output,
        args,  # Parsed arguments
    ):
        self._activities = activities
        self._now = now
        self._output = output
        self._args = args

    def __call__(self):
        # Filter working activities
        work_activities = [a for a in self._activities if a.type == _v1.Activity.Type.WORK]

        # Calculate total worked time
        worked_time = sum((a.duration for a in work_activities), timedelta())

        # Calculate remaining vs target
        target = timedelta(hours=self._args.daily_hours)
        remaining = target - worked_time

        # Display with Rich
        self._display(worked_time, remaining)
```

### Key Differences from Current Implementation

| Aspect | Current (`check_time`) | New (`utt-balance`) |
|--------|----------------------|---------------------|
| Data access | Subprocess + regex parsing | Direct API injection |
| Performance | Slow (spawns process) | Fast (in-process) |
| Reliability | Fragile (depends on text format) | Robust (typed objects) |
| Integration | Standalone CLI | Native UTT command |
| Installation | Manual | `pip install utt-balance` |

---

## Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "utt-balance"
version = "0.1.0"
description = "A UTT plugin to check worked time balance against daily/weekly targets"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
dependencies = [
    "utt",
    "rich",
]

[project.urls]
Homepage = "https://github.com/loganthomas/utt-balance"
Repository = "https://github.com/loganthomas/utt-balance"

[tool.setuptools.packages.find]
where = ["src"]
include = ["utt_balance*", "utt*"]

[tool.setuptools.package-dir]
"" = "src"
```

---

## File Structure (Final)

```
utt-balance/
├── .github/
│   └── workflows/
│       └── publish.yml       # PyPI publish workflow
├── src/
│   ├── utt_balance/
│   │   └── __init__.py       # Version and package info
│   └── utt/
│       ├── __init__.py       # Empty (namespace package)
│       └── plugins/
│           ├── __init__.py   # Empty (namespace package)
│           └── balance.py    # The plugin command
├── tests/
│   └── test_balance.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

---

## Timeline Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Project Setup | 30 minutes |
| 2 | Core Plugin Development | 2-3 hours |
| 3 | Output & Display | 1 hour |
| 4 | Testing | 1-2 hours |
| 5 | Documentation & Publishing | 1 hour |
| **Total** | | **5-7 hours** |

---

## Next Steps

1. **Confirm the name**: Do you want to go with `utt-balance`?
2. **Choose license**: MIT, GPL-3.0, or other?
3. **Confirm features**: Any additional features beyond daily/weekly balance?
4. **Start implementation**: Begin with Phase 1

---

## Questions to Consider

1. Should the plugin support custom work day definitions (e.g., Mon-Fri vs Mon-Sat)?
2. Do you want configurable targets via UTT's config file or just CLI args?
3. Should it show historical data (e.g., balance for previous weeks)?
4. Do you want an option to hide the current in-progress activity?
