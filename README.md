# utt-balance

[![CI - Test](https://github.com/loganthomas/utt-balance/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/loganthomas/utt-balance/actions/workflows/unit-tests.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/utt-balance.svg)](https://pypi.org/project/utt-balance/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/utt-balance.svg?label=PyPI%20downloads)](https://pypi.org/project/utt-balance/)
[![License - GPL-3.0](https://img.shields.io/pypi/l/utt-balance.svg)](https://github.com/loganthomas/utt-balance/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/utt-balance.svg)](https://pypi.org/project/utt-balance/)

A [`utt`](https://github.com/larose/utt) plugin that shows your worked time balance against daily and weekly targets.

## Why utt-balance?

This plugin is designed as a quick time check to see how many hours you've worked and what your remaining time budget is. The name "balance" reflects its core purpose: supporting your work-life balance by encouraging you to stay within your pre-allocated work time.

**The color coding tells the story:**

- **🟢 Green** — You're under your target. You still have time remaining in your budget for the day or week.
- **🟡 Yellow** — You've hit exactly your target. This is a warning that you're about to dip into a deficit.
- **🔴 Red** — You've exceeded your allotted time. You're over 8 hours for the day or 40 hours for the week (by default).

Work ebbs and flows—certain days are more demanding than others, and that's okay. But having a quick visual check helps keep things on rails and reminds you to protect your time outside of work.

## Features

- 📊 **Daily & Weekly Tracking** - See worked hours and remaining time at a glance
- 🎨 **Color-coded Output** - Green (under target), Yellow (at target), Red (over/negative)
- ⚙️ **Configurable Targets** - Set custom daily hours, weekly hours, and week start day
- 🔌 **Native `utt` Integration** - Uses `utt`'s plugin API for seamless integration

## Installation

### Step 1: Install `utt`

First, install [`utt` (Ultimate Time Tracker)](https://github.com/larose/utt):

```bash
pip install utt
```

Verify the installation:

```bash
utt --version
```

### Step 2: Install utt-balance

Install the plugin:

```bash
pip install utt-balance
```

That's it! The plugin is automatically discovered by `utt`. No additional configuration needed.

### Verify Installation

Confirm the `balance` command is available:

```bash
utt balance --help
```

**Requirements:**
- Python 3.10+
- `utt` >= 1.0

## Usage

After installation, a new `balance` command is available in `utt`:

```bash
utt balance
```

### Example Output

**🟢 Under target — time remaining in your budget:**

![Under target](docs/images/under-target-example.webp)

**🟡 At target — you've hit your limit:**

![At target](docs/images/at-target-example.webp)

**🔴 Over target — you've exceeded your budget:**

![Over target](docs/images/over-target-example.webp)

### Options

| Option         | Default  | Description                    |
|----------------|----------|--------------------------------|
| `--daily-hrs`  | 8        | Target working hours per day   |
| `--weekly-hrs` | 40       | Target working hours per week  |
| `--week-start` | sunday   | Day the work week starts       |

> [!NOTE]
> **`--week-start` values:** `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

### Examples

**Default usage** (8h/day, 40h/week, week starts Sunday):
```bash
utt balance
```

**Custom daily target** — set a 6-hour workday with `--daily-hrs`:
```bash
utt balance --daily-hrs 6
```
```
┌──────────────┬─────────┬───────────┐
│              │  Worked │ Remaining │
├──────────────┼─────────┼───────────┤
│ Today        │   5h00  │     1h00  │  ← 1h until 6h target
│ Since Sunday │  25h00  │    15h00  │
└──────────────┴─────────┴───────────┘
```

**Custom weekly target** — set a 35-hour work week with `--weekly-hrs`:
```bash
utt balance --weekly-hrs 35
```
```
┌──────────────┬─────────┬───────────┐
│              │  Worked │ Remaining │
├──────────────┼─────────┼───────────┤
│ Today        │   6h30  │     1h30  │
│ Since Sunday │  28h00  │     7h00  │  ← 7h until 35h target
└──────────────┴─────────┴───────────┘
```

**Change week start day** — use Monday with `--week-start`:
```bash
utt balance --week-start monday
```
```
┌──────────────┬─────────┬───────────┐
│              │  Worked │ Remaining │
├──────────────┼─────────┼───────────┤
│ Today        │   6h30  │     1h30  │
│ Since Monday │  22h30  │    17h30  │  ← week starts Monday
└──────────────┴─────────┴───────────┘
```

**Part-time schedule** — combine options for 4h/day, 20h/week:
```bash
utt balance --daily-hrs 4 --weekly-hrs 20
```
```
┌──────────────┬─────────┬───────────┐
│              │  Worked │ Remaining │
├──────────────┼─────────┼───────────┤
│ Today        │   3h30  │     0h30  │  ← 30min until 4h target
│ Since Sunday │  15h00  │     5h00  │  ← 5h until 20h target
└──────────────┴─────────┴───────────┘
```

## Color Coding

| Color | Worked Column | Remaining Column |
|-------|--------------|------------------|
| 🟢 Green | Under target | Time remaining |
| 🟡 Yellow | Exactly at target | Zero remaining |
| 🔴 Red | Over target | Negative (overtime) |

## How It Works

This plugin uses `utt`'s native plugin API to:
1. Access your time entries directly (no subprocess calls)
2. Filter activities for today and the current week
3. Calculate total working time (excludes breaks marked with `**`)
4. Compare against your configured targets

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Development

### Running Tests

To run the test suite, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run the tests with pytest:

```bash
pytest
```

For coverage reporting:

```bash
pytest --cov=utt_balance.balance --cov-report=term-missing
```

### Linting & Formatting

**Run ruff** (linter, formatter, and import sorting):
```bash
# Check for linting errors
ruff check .

# Auto-fix linting errors (including import sorting)
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

**Run ty** (type checker):
```bash
ty check src/
```

### Run All Checks

```bash
ruff check --fix . && ruff format . && ty check src/ && pytest
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run checks before each commit:

```bash
pre-commit install
```

Run hooks manually on all files:

```bash
pre-commit run --all-files
```

## Contributing

Contributions are welcome! Here's how to get started:

### Setting Up for Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/loganthomas/utt-balance.git
   cd utt-balance
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in editable mode with dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### Submitting Changes

1. Create a new branch for your feature or fix
2. Make your changes following the code style guidelines
3. Ensure all tests pass: `pytest`
4. Ensure code passes linting: `ruff check . && ruff format --check .`
5. Submit a pull request with a clear description of your changes

### Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for all function signatures
- Write docstrings in [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html)
- Keep functions focused and single-purpose
- Prefer explicit over implicit

## Related

- [`utt` (Ultimate Time Tracker)](https://github.com/larose/utt) - The time tracking tool this plugin extends
- [`utt` Plugin Documentation](https://github.com/larose/utt/blob/master/docs/PLUGINS.md) - How to create `utt` plugins
