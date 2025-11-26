"""
UTT Balance Plugin - Check worked time balance against daily/weekly targets.

This plugin adds a 'balance' command to UTT that displays worked hours
and remaining time for today and the current week with color-coded output.
"""
import argparse
import datetime
from typing import List

from rich.console import Console
from rich.table import Table
from rich.text import Text

from utt.api import _v1


class BalanceHandler:
    """Handler for the balance command that displays worked time vs targets."""

    def __init__(
        self,
        args: argparse.Namespace,
        now: _v1.Now,
        entries: _v1.Entries,
        output: _v1.Output,
    ):
        self._args = args
        self._now = now
        self._entries = entries
        self._output = output

    def __call__(self) -> None:
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
        """Calculate the start date of the current week based on configured week start day."""
        day_names = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"
        ]
        week_start_index = day_names.index(self._args.week_start.lower())
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
            a for a in activities
            if a.type == _v1.Activity.Type.WORK
            and a.name.name != _v1.HELLO_ENTRY_NAME
        ]
        return sum((a.duration for a in work_activities), datetime.timedelta())

    def _get_activities_for_range(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> List[_v1.Activity]:
        """Get activities within the specified date range."""
        activities = list(self._entries_to_activities())
        return self._filter_and_clip_activities(activities, start_date, end_date)

    def _entries_to_activities(self):
        """Convert entries to activities (activity spans between consecutive entries)."""
        entries = list(self._entries)
        for i in range(len(entries) - 1):
            prev_entry = entries[i]
            next_entry = entries[i + 1]
            yield _v1.Activity(
                next_entry.name,
                prev_entry.datetime,
                next_entry.datetime,
                False,
            )

    def _filter_and_clip_activities(
        self,
        activities: List[_v1.Activity],
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> List[_v1.Activity]:
        """Filter activities to date range and clip those that span boundaries."""
        start_dt = datetime.datetime(
            start_date.year, start_date.month, start_date.day
        )
        end_dt = datetime.datetime(
            end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999
        )

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
        """Display the balance table with color-coded values."""
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
        self, worked: datetime.timedelta, target: datetime.timedelta
    ) -> Text:
        """Format worked time with appropriate color based on target."""
        text = self._format_timedelta(worked)
        if worked == target:
            return Text(text, style="yellow3")
        elif worked > target:
            return Text(text, style="red")
        return Text(text, style="green")

    def _format_remaining(self, remaining: datetime.timedelta) -> Text:
        """Format remaining time with appropriate color."""
        is_negative = remaining < datetime.timedelta()
        text = self._format_timedelta(remaining)
        if remaining == datetime.timedelta():
            return Text(text, style="yellow3")
        elif is_negative:
            return Text(text, style="red")
        return Text(text, style="green")

    @staticmethod
    def _format_timedelta(td: datetime.timedelta) -> str:
        """Format a timedelta as 'XhYY' (e.g., '6h30' or '-1h15')."""
        total_seconds = int(td.total_seconds())
        is_negative = total_seconds < 0
        total_seconds = abs(total_seconds)

        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        result = f"{hours}h{minutes:02d}"
        return f"-{result}" if is_negative else result


def add_args(parser: argparse.ArgumentParser) -> None:
    """Add command-line arguments for the balance command."""
    parser.add_argument(
        "--daily-hrs",
        type=float,
        default=8,
        help="Target working hours per day (default: 8)",
    )
    parser.add_argument(
        "--weekly-hrs",
        type=float,
        default=40,
        help="Target working hours per week (default: 40)",
    )
    parser.add_argument(
        "--week-start",
        type=str,
        default="sunday",
        choices=[
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"
        ],
        help="Day the work week starts (default: sunday)",
    )


balance_command = _v1.Command(
    name="balance",
    description="Show worked time balance against daily/weekly targets",
    handler_class=BalanceHandler,
    add_args=add_args,
)

_v1.register_command(balance_command)
