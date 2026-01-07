"""
utt Balance Plugin - Check worked time balance against daily/weekly targets.

This plugin adds a 'balance' command to utt that displays worked hours
and remaining time for today and the current week with color-coded output.

Example
-------
>>> utt balance
>>> utt balance --daily-hrs 6 --weekly-hrs 30 --week-start monday
"""

from __future__ import annotations

import argparse
import datetime
from collections.abc import Iterator
from itertools import pairwise

from rich.console import Console
from rich.table import Table
from rich.text import Text

from utt.api import _v1

# Day names in weekday order (Monday=0 through Sunday=6)
DAY_NAMES: tuple[str, ...] = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

# Rich color styles for output
STYLE_UNDER_TARGET: str = "green"
STYLE_AT_TARGET: str = "yellow3"
STYLE_OVER_TARGET: str = "red"

# Default target hours
DEFAULT_DAILY_HOURS: float = 8.0
DEFAULT_WEEKLY_HOURS: float = 40.0
DEFAULT_WEEK_START: str = "sunday"


class BalanceHandler:
    """
    Handler for the balance command that displays worked time vs targets.

    This handler calculates the total time worked for today and the current
    week, then displays the results in a color-coded table showing both
    worked time and remaining time until targets are met.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments containing daily_hrs, weekly_hrs,
        and week_start configuration.
    now : _v1.Now
        Current datetime provided by utt's dependency injection.
    entries : _v1.Entries
        Time entries from the utt log file.
    output : _v1.Output
        Output stream for rendering the results table.

    Examples
    --------
    The handler is typically instantiated by utt's plugin system:

    >>> handler = BalanceHandler(args, now, entries, output)
    >>> handler()  # Displays the balance table
    """

    def __init__(
        self,
        args: argparse.Namespace,
        now: _v1.Now,
        entries: _v1.Entries,
        output: _v1.Output,
    ) -> None:
        self._args = args
        self._now = now
        self._entries = entries
        self._output = output

    def __call__(self) -> None:
        """Execute the balance command and display results."""
        today = self._now.date()
        week_start = self._get_week_start_date(today)

        worked_today = self._calculate_worked_time(today, today)
        worked_week = self._calculate_worked_time(week_start, today)

        daily_target = datetime.timedelta(hours=self._args.daily_hrs)
        weekly_target = datetime.timedelta(hours=self._args.weekly_hrs)

        remaining_today = daily_target - worked_today
        remaining_week = weekly_target - worked_week

        self._display_table(
            worked_today=worked_today,
            remaining_today=remaining_today,
            worked_week=worked_week,
            remaining_week=remaining_week,
            week_start_day=self._args.week_start.capitalize(),
        )

    def _get_week_start_date(self, today: datetime.date) -> datetime.date:
        """
        Calculate the start date of the current week.

        Uses the configured week start day to determine when the current
        work week began.

        Parameters
        ----------
        today : datetime.date
            The current date.

        Returns
        -------
        datetime.date
            The date when the current week started based on the configured
            week start day.

        Examples
        --------
        If today is Wednesday and week_start is "sunday":

        >>> handler._get_week_start_date(date(2025, 11, 26))
        datetime.date(2025, 11, 23)  # Previous Sunday
        """
        week_start_index = DAY_NAMES.index(self._args.week_start.lower())
        today_index = today.weekday()

        days_since_week_start = (today_index - week_start_index) % 7
        return today - datetime.timedelta(days=days_since_week_start)

    def _calculate_worked_time(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> datetime.timedelta:
        """
        Calculate total working time for a date range.

        Filters activities to only include WORK type activities (excluding
        breaks and hello entries) and sums their durations.

        Parameters
        ----------
        start_date : datetime.date
            Start of the date range (inclusive).
        end_date : datetime.date
            End of the date range (inclusive).

        Returns
        -------
        datetime.timedelta
            Total working time excluding breaks and hello entries.
        """
        activities = self._get_activities_for_range(start_date, end_date)
        work_activities = [
            activity
            for activity in activities
            if activity.type == _v1.Activity.Type.WORK
            and activity.name.name != _v1.HELLO_ENTRY_NAME
        ]
        return sum((activity.duration for activity in work_activities), datetime.timedelta())

    def _get_activities_for_range(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[_v1.Activity]:
        """
        Get activities within the specified date range.

        Parameters
        ----------
        start_date : datetime.date
            Start of the date range (inclusive).
        end_date : datetime.date
            End of the date range (inclusive).

        Returns
        -------
        list[_v1.Activity]
            Activities that fall within or overlap the date range,
            clipped to the range boundaries.
        """
        activities = list(self._entries_to_activities())
        return self._filter_and_clip_activities(activities, start_date, end_date)

    def _entries_to_activities(self) -> Iterator[_v1.Activity]:
        """
        Convert entries to activities.

        An activity spans between two consecutive entries, with the second
        entry's name being the activity name and the time difference being
        the activity duration.

        Yields
        ------
        _v1.Activity
            Activity objects derived from consecutive entry pairs.
        """
        for prev_entry, next_entry in pairwise(self._entries):
            yield _v1.Activity(
                next_entry.name,
                prev_entry.datetime,
                next_entry.datetime,
                False,
                next_entry.comment,
            )

    def _filter_and_clip_activities(
        self,
        activities: list[_v1.Activity],
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[_v1.Activity]:
        """
        Filter activities to date range and clip those spanning boundaries.

        Activities that partially overlap the date range are clipped to only
        include the portion within the range. Activities fully outside the
        range are excluded.

        Parameters
        ----------
        activities : list[_v1.Activity]
            All activities to filter.
        start_date : datetime.date
            Start of the date range (inclusive).
        end_date : datetime.date
            End of the date range (inclusive).

        Returns
        -------
        list[_v1.Activity]
            Activities within the range, with boundary-spanning activities
            clipped to the range.
        """
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        result = []
        for activity in activities:
            clipped = activity.clip(start_dt, end_dt)
            if clipped.duration > datetime.timedelta():
                result.append(clipped)
        return result

    def _display_table(
        self,
        worked_today: datetime.timedelta,
        remaining_today: datetime.timedelta,
        worked_week: datetime.timedelta,
        remaining_week: datetime.timedelta,
        week_start_day: str,
    ) -> None:
        """
        Display the balance table with color-coded values.

        Parameters
        ----------
        worked_today : datetime.timedelta
            Time worked today.
        remaining_today : datetime.timedelta
            Time remaining until daily target.
        worked_week : datetime.timedelta
            Time worked this week.
        remaining_week : datetime.timedelta
            Time remaining until weekly target.
        week_start_day : str
            Capitalized name of the week start day for display.
        """
        table = Table()
        table.add_column("")
        table.add_column("Worked", justify="right")
        table.add_column("Remaining", justify="right")

        daily_target = datetime.timedelta(hours=self._args.daily_hrs)
        weekly_target = datetime.timedelta(hours=self._args.weekly_hrs)

        table.add_row(
            "Today",
            self._format_worked(worked_today, daily_target),
            self._format_remaining(remaining_today),
        )
        table.add_row(
            f"Since {week_start_day}",
            self._format_worked(worked_week, weekly_target),
            self._format_remaining(remaining_week),
        )

        console = Console(file=self._output)
        console.print(table)

    def _format_worked(
        self,
        worked: datetime.timedelta,
        target: datetime.timedelta,
    ) -> Text:
        """
        Format worked time with appropriate color based on target.

        Parameters
        ----------
        worked : datetime.timedelta
            Time worked.
        target : datetime.timedelta
            Target time to compare against.

        Returns
        -------
        rich.text.Text
            Formatted text with color style:
            - Green: under target
            - Yellow: exactly at target
            - Red: over target
        """
        text = self._format_timedelta(worked)
        if worked == target:
            return Text(text, style=STYLE_AT_TARGET)
        elif worked > target:
            return Text(text, style=STYLE_OVER_TARGET)
        return Text(text, style=STYLE_UNDER_TARGET)

    def _format_remaining(self, remaining: datetime.timedelta) -> Text:
        """
        Format remaining time with appropriate color.

        Parameters
        ----------
        remaining : datetime.timedelta
            Time remaining (can be negative if over target).

        Returns
        -------
        rich.text.Text
            Formatted text with color style:
            - Green: positive remaining time
            - Yellow: exactly zero remaining
            - Red: negative (overtime)
        """
        is_negative = remaining < datetime.timedelta()
        text = self._format_timedelta(remaining)
        if remaining == datetime.timedelta():
            return Text(text, style=STYLE_AT_TARGET)
        elif is_negative:
            return Text(text, style=STYLE_OVER_TARGET)
        return Text(text, style=STYLE_UNDER_TARGET)

    @staticmethod
    def _format_timedelta(td: datetime.timedelta) -> str:
        """
        Format a timedelta as 'XhYY' (e.g., '6h30' or '-1h15').

        Parameters
        ----------
        td : datetime.timedelta
            The time duration to format.

        Returns
        -------
        str
            Formatted string in hours and zero-padded minutes.

        Examples
        --------
        >>> BalanceHandler._format_timedelta(timedelta(hours=6, minutes=30))
        '6h30'
        >>> BalanceHandler._format_timedelta(timedelta(hours=-2, minutes=-15))
        '-2h15'
        """
        total_seconds = int(td.total_seconds())
        is_negative = total_seconds < 0
        total_seconds = abs(total_seconds)

        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        result = f"{hours}h{minutes:02d}"
        return f"-{result}" if is_negative else result


def add_args(parser: argparse.ArgumentParser) -> None:
    """
    Add command-line arguments for the balance command.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The argument parser to add arguments to.
    """
    parser.add_argument(
        "--daily-hrs",
        type=float,
        default=DEFAULT_DAILY_HOURS,
        metavar="HOURS",
        help=f"Target working hours per day (default: {DEFAULT_DAILY_HOURS:.0f})",
    )
    parser.add_argument(
        "--weekly-hrs",
        type=float,
        default=DEFAULT_WEEKLY_HOURS,
        metavar="HOURS",
        help=f"Target working hours per week (default: {DEFAULT_WEEKLY_HOURS:.0f})",
    )
    parser.add_argument(
        "--week-start",
        type=str,
        default=DEFAULT_WEEK_START,
        choices=DAY_NAMES,
        help=f"Day the work week starts (default: {DEFAULT_WEEK_START})",
    )


# Register the balance command with utt
balance_command = _v1.Command(
    name="balance",
    description="Show worked time balance against daily/weekly targets",
    handler_class=BalanceHandler,  # type: ignore[arg-type]
    add_args=add_args,
)

_v1.register_command(balance_command)
