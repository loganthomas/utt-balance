"""Unit tests for the balance plugin."""

import argparse
import datetime
import io

import pytest

from utt.api import _v1
from utt.plugins.balance import BalanceHandler, add_args, balance_command


@pytest.fixture
def mock_args():
    """Create mock command-line arguments with default values."""
    args = argparse.Namespace()
    args.daily_hrs = 8
    args.weekly_hrs = 40
    args.week_start = "sunday"
    return args


@pytest.fixture
def mock_output():
    """Create a StringIO object to capture output."""
    return io.StringIO()


class TestFormatTimedelta:
    """Tests for the _format_timedelta static method."""

    def test_zero_time(self):
        td = datetime.timedelta(hours=0)
        assert BalanceHandler._format_timedelta(td) == "0h00"

    def test_whole_hours(self):
        td = datetime.timedelta(hours=8)
        assert BalanceHandler._format_timedelta(td) == "8h00"

    def test_hours_and_minutes(self):
        td = datetime.timedelta(hours=6, minutes=30)
        assert BalanceHandler._format_timedelta(td) == "6h30"

    def test_minutes_only(self):
        td = datetime.timedelta(minutes=45)
        assert BalanceHandler._format_timedelta(td) == "0h45"

    def test_negative_time(self):
        td = datetime.timedelta(hours=-2, minutes=-15)
        assert BalanceHandler._format_timedelta(td) == "-2h15"

    def test_large_hours(self):
        td = datetime.timedelta(hours=40)
        assert BalanceHandler._format_timedelta(td) == "40h00"

    def test_single_digit_minutes_padded(self):
        td = datetime.timedelta(hours=1, minutes=5)
        assert BalanceHandler._format_timedelta(td) == "1h05"


class TestGetWeekStartDate:
    """Tests for week start date calculation."""

    def test_sunday_week_start_on_wednesday(self, mock_args, mock_output):
        # Wednesday Nov 26, 2025
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        mock_args.week_start = "sunday"

        handler = BalanceHandler(mock_args, now, [], mock_output)
        week_start = handler._get_week_start_date(now.date())

        # Should be Sunday Nov 23, 2025
        assert week_start == datetime.date(2025, 11, 23)

    def test_monday_week_start_on_wednesday(self, mock_args, mock_output):
        # Wednesday Nov 26, 2025
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        mock_args.week_start = "monday"

        handler = BalanceHandler(mock_args, now, [], mock_output)
        week_start = handler._get_week_start_date(now.date())

        # Should be Monday Nov 24, 2025
        assert week_start == datetime.date(2025, 11, 24)

    def test_week_start_same_as_today(self, mock_args, mock_output):
        # Sunday Nov 23, 2025
        now = datetime.datetime(2025, 11, 23, 12, 0, 0)
        mock_args.week_start = "sunday"

        handler = BalanceHandler(mock_args, now, [], mock_output)
        week_start = handler._get_week_start_date(now.date())

        # Should be the same day
        assert week_start == datetime.date(2025, 11, 23)

    def test_friday_week_start(self, mock_args, mock_output):
        # Wednesday Nov 26, 2025
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        mock_args.week_start = "friday"

        handler = BalanceHandler(mock_args, now, [], mock_output)
        week_start = handler._get_week_start_date(now.date())

        # Should be Friday Nov 21, 2025
        assert week_start == datetime.date(2025, 11, 21)


class TestEntriesToActivities:
    """Tests for converting entries to activities."""

    def test_two_entries_one_activity(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 1
        assert activities[0].name.name == "work: task"
        assert activities[0].duration == datetime.timedelta(hours=8)

    def test_three_entries_two_activities(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 12, 0), "lunch **", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 13, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 2
        assert activities[0].name.name == "lunch **"
        assert activities[0].duration == datetime.timedelta(hours=3)
        assert activities[1].name.name == "work: task"
        assert activities[1].duration == datetime.timedelta(hours=1)

    def test_single_entry_no_activities(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 9, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 0

    def test_empty_entries(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 9, 0, 0)
        entries = []

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 0

    def test_activity_preserves_entry_comment(self, mock_args, mock_output):
        """Regression test: Activity must include comment from Entry.

        This test ensures that when entries with comments are converted to
        activities, the comment is properly passed through. Without this,
        the Activity constructor raises TypeError for missing 'comment' arg.
        """
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(
                datetime.datetime(2025, 11, 26, 17, 0),
                "work: task",
                False,
                "working on feature X",
            ),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 1
        assert activities[0].comment == "working on feature X"

    def test_activity_handles_none_comment(self, mock_args, mock_output):
        """Regression test: Activity handles None comment gracefully."""
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())

        assert len(activities) == 1
        assert activities[0].comment is None


class TestCalculateWorkedTime:
    """Tests for worked time calculation."""

    def test_excludes_breaks(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 12, 0), "lunch **", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 13, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        worked = handler._calculate_worked_time(
            datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        # Only "work: task" (1h) should be counted, not "lunch **" (3h break)
        assert worked == datetime.timedelta(hours=1)

    def test_excludes_hello_entries(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 25, 17, 0), "work: done", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        worked = handler._calculate_worked_time(
            datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        # Overnight "hello" activity should be excluded
        assert worked == datetime.timedelta(hours=8)

    def test_full_work_day(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        worked = handler._calculate_worked_time(
            datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        assert worked == datetime.timedelta(hours=8)

    def test_no_entries(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 9, 0, 0)
        entries = []

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        worked = handler._calculate_worked_time(
            datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        assert worked == datetime.timedelta()


class TestFilterAndClipActivities:
    """Tests for activity filtering and clipping."""

    def test_clips_activity_spanning_date_boundary(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 25, 22, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 2, 0), "work: late", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())
        filtered = handler._filter_and_clip_activities(
            activities, datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        # Activity spans from Nov 25 22:00 to Nov 26 02:00
        # Only 2 hours fall on Nov 26 (midnight to 02:00)
        assert len(filtered) == 1
        assert filtered[0].duration == datetime.timedelta(hours=2)

    def test_excludes_activities_fully_outside_range(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 24, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 24, 17, 0), "work: old", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 25, 9, 0), "hello", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())
        filtered = handler._filter_and_clip_activities(
            activities, datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        # Activities entirely before Nov 26 should be excluded
        assert len(filtered) == 0

    def test_clips_overnight_activity_into_range(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 25, 17, 0), "work: old", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: today", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        activities = list(handler._entries_to_activities())
        filtered = handler._filter_and_clip_activities(
            activities, datetime.date(2025, 11, 26), datetime.date(2025, 11, 26)
        )

        # Overnight "hello" gets clipped to Nov 26 portion, plus "work: today"
        assert len(filtered) == 2
        assert filtered[0].name.name == "hello"
        assert filtered[0].duration == datetime.timedelta(hours=9)  # midnight to 9am
        assert filtered[1].name.name == "work: today"


class TestFormatWorked:
    """Tests for worked time formatting with colors."""

    def test_under_target_is_green(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        worked = datetime.timedelta(hours=4)
        target = datetime.timedelta(hours=8)
        result = handler._format_worked(worked, target)

        assert result.style == "green"

    def test_at_target_is_yellow(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        worked = datetime.timedelta(hours=8)
        target = datetime.timedelta(hours=8)
        result = handler._format_worked(worked, target)

        assert result.style == "yellow3"

    def test_over_target_is_red(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 19, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        worked = datetime.timedelta(hours=10)
        target = datetime.timedelta(hours=8)
        result = handler._format_worked(worked, target)

        assert result.style == "red"


class TestFormatRemaining:
    """Tests for remaining time formatting with colors."""

    def test_positive_remaining_is_green(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        remaining = datetime.timedelta(hours=4)
        result = handler._format_remaining(remaining)

        assert result.style == "green"

    def test_zero_remaining_is_yellow(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        remaining = datetime.timedelta()
        result = handler._format_remaining(remaining)

        assert result.style == "yellow3"

    def test_negative_remaining_is_red(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 19, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        remaining = datetime.timedelta(hours=-2)
        result = handler._format_remaining(remaining)

        assert result.style == "red"


class TestDisplayTable:
    """Tests for the _display_table method."""

    def test_display_table_outputs_to_stream(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 12, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        handler._display_table(
            worked_today=datetime.timedelta(hours=4),
            remaining_today=datetime.timedelta(hours=4),
            worked_week=datetime.timedelta(hours=20),
            remaining_week=datetime.timedelta(hours=20),
            week_start_day="Sunday",
        )

        output = mock_output.getvalue()
        assert "Today" in output
        assert "Since Sunday" in output
        assert "Worked" in output
        assert "Remaining" in output

    def test_display_table_shows_correct_values(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        handler = BalanceHandler(mock_args, now, [], mock_output)

        handler._display_table(
            worked_today=datetime.timedelta(hours=8),
            remaining_today=datetime.timedelta(hours=0),
            worked_week=datetime.timedelta(hours=32),
            remaining_week=datetime.timedelta(hours=8),
            week_start_day="Monday",
        )

        output = mock_output.getvalue()
        assert "8h00" in output
        assert "32h00" in output
        assert "Since Monday" in output


class TestCall:
    """Tests for the __call__ method (main entry point)."""

    def test_call_with_full_work_day(self, mock_args, mock_output):
        # Wednesday Nov 26, 2025
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        handler()

        output = mock_output.getvalue()
        assert "Today" in output
        assert "8h00" in output

    def test_call_with_week_data(self, mock_args, mock_output):
        # Wednesday Nov 26, 2025 (week starts Sunday Nov 23)
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        mock_args.week_start = "sunday"
        entries = [
            # Monday
            _v1.Entry(datetime.datetime(2025, 11, 24, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 24, 17, 0), "work: mon", False, None),
            # Tuesday
            _v1.Entry(datetime.datetime(2025, 11, 25, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 25, 17, 0), "work: tue", False, None),
            # Wednesday
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 17, 0), "work: wed", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        handler()

        output = mock_output.getvalue()
        assert "Since Sunday" in output
        # 3 days * 8 hours = 24 hours worked
        assert "24h00" in output

    def test_call_with_no_entries(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 9, 0, 0)
        entries = []

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        handler()

        output = mock_output.getvalue()
        assert "Today" in output
        assert "0h00" in output

    def test_call_with_custom_targets(self, mock_args, mock_output):
        now = datetime.datetime(2025, 11, 26, 17, 0, 0)
        mock_args.daily_hrs = 6
        mock_args.weekly_hrs = 30
        entries = [
            _v1.Entry(datetime.datetime(2025, 11, 26, 9, 0), "hello", False, None),
            _v1.Entry(datetime.datetime(2025, 11, 26, 15, 0), "work: task", False, None),
        ]

        handler = BalanceHandler(mock_args, now, entries, mock_output)
        handler()

        output = mock_output.getvalue()
        # 6 hours worked, 6 hour target = 0h00 remaining
        assert "6h00" in output
        assert "0h00" in output


class TestAddArgs:
    """Tests for the add_args function."""

    def test_adds_daily_hrs_argument(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args([])
        assert args.daily_hrs == 8

    def test_adds_weekly_hrs_argument(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args([])
        assert args.weekly_hrs == 40

    def test_adds_week_start_argument(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args([])
        assert args.week_start == "sunday"

    def test_daily_hrs_custom_value(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args(["--daily-hrs", "6"])
        assert args.daily_hrs == 6.0

    def test_weekly_hrs_custom_value(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args(["--weekly-hrs", "35"])
        assert args.weekly_hrs == 35.0

    def test_week_start_custom_value(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        args = parser.parse_args(["--week-start", "monday"])
        assert args.week_start == "monday"

    def test_week_start_invalid_value_raises(self):
        parser = argparse.ArgumentParser()
        add_args(parser)

        with pytest.raises(SystemExit):
            parser.parse_args(["--week-start", "invalid"])


class TestBalanceCommand:
    """Tests for the balance command registration."""

    def test_command_name(self):
        assert balance_command.name == "balance"

    def test_command_description(self):
        assert "balance" in balance_command.description.lower()

    def test_command_handler_class(self):
        assert balance_command.handler_class == BalanceHandler

    def test_command_add_args(self):
        assert balance_command.add_args == add_args
