# utt-balance

A [UTT](https://github.com/larose/utt) plugin that shows your worked time balance against daily and weekly targets.

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
- 🔌 **Native UTT Integration** - Uses UTT's plugin API for seamless integration

## Installation

### Step 1: Install UTT

First, install [UTT (Ultimate Time Tracker)](https://github.com/larose/utt):

```bash
pip install utt
```

Verify the installation:

```bash
utt --help
```

### Step 2: Install utt-balance

Install the plugin:

```bash
pip install utt-balance
```

That's it! The plugin is automatically discovered by UTT. No additional configuration needed.

### Verify Installation

Confirm the `balance` command is available:

```bash
utt balance --help
```

**Requirements:**
- Python 3.10+
- UTT >= 1.0

## Usage

After installation, a new `balance` command is available in UTT:

```bash
utt balance
```

### Example Output

```
┌──────────────┬─────────┬───────────┐
│              │  Worked │ Remaining │
├──────────────┼─────────┼───────────┤
│ Today        │   6h30  │     1h30  │
│ Since Sunday │  32h15  │     7h45  │
└──────────────┴─────────┴───────────┘
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--daily-hrs` | 8 | Target working hours per day |
| `--weekly-hrs` | 40 | Target working hours per week |
| `--week-start` | sunday | Day the work week starts |

### Examples

**Custom daily target (6 hours):**
```bash
utt balance --daily-hrs 6
```

**Custom weekly target with Monday as week start:**
```bash
utt balance --weekly-hrs 35 --week-start monday
```

**Part-time schedule (4 hours/day, 20 hours/week):**
```bash
utt balance --daily-hrs 4 --weekly-hrs 20
```

## Color Coding

| Color | Worked Column | Remaining Column |
|-------|--------------|------------------|
| 🟢 Green | Under target | Time remaining |
| 🟡 Yellow | Exactly at target | Zero remaining |
| 🔴 Red | Over target | Negative (overtime) |

## How It Works

This plugin uses UTT's native plugin API to:
1. Access your time entries directly (no subprocess calls)
2. Filter activities for today and the current week
3. Calculate total working time (excludes breaks marked with `**`)
4. Compare against your configured targets

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

MIT is compatible with UTT's GPL-3.0 license, allowing maximum flexibility for users.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related

- [UTT (Ultimate Time Tracker)](https://github.com/larose/utt) - The time tracking tool this plugin extends
- [UTT Plugin Documentation](https://github.com/larose/utt/blob/master/docs/PLUGINS.md) - How to create UTT plugins

