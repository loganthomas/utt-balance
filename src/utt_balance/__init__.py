"""
utt-balance: A UTT plugin to check worked time balance against daily/weekly targets.

This plugin adds a 'balance' command to UTT that shows:
- Worked hours for today and the current week
- Remaining hours until daily/weekly targets
- Color-coded output (green=under, yellow=at, red=over target)

Usage:
    utt balance [--daily-hrs HOURS] [--weekly-hrs HOURS] [--week-start DAY]

For more information, see: https://github.com/loganthomas/utt-balance
"""

__version__ = "0.1.0"
__author__ = "Logan Thomas"
__email__ = "logan@datacentriq.net"
