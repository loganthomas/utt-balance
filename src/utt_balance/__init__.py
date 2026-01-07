"""
utt-balance: A utt plugin to check worked time balance against daily/weekly targets.

This plugin adds a 'balance' command to utt that shows:

- Worked hours for today and the current week
- Remaining hours until daily/weekly targets
- Color-coded output (green=under, yellow=at, red=over target)

Installation
------------
Install via pip::

    pip install utt-balance

Usage
-----
After installation, the balance command is available via utt::

    utt balance [--daily-hrs HOURS] [--weekly-hrs HOURS] [--week-start DAY]

Examples
--------
Check balance with default settings (8h/day, 40h/week)::

    utt balance

Check with custom targets::

    utt balance --daily-hrs 6 --weekly-hrs 30 --week-start monday

For more information, see: https://github.com/loganthomas/utt-balance
"""

__version__ = "0.1.1"

__all__ = ["__version__"]
