from datetime import UTC, datetime, timedelta
from pathlib import Path


def test_schedule_uses_latest_pull_up_set(tmp_path: Path) -> None:
    from pull_up.database import Storage
    from pull_up.schedule import IncrementingExerciseSchedule

    storage = Storage(tmp_path / "pull_ups.csv")
    schedule = IncrementingExerciseSchedule("pull-up")
    ts = datetime(2026, 1, 10, tzinfo=UTC)
    day = ts.date()

    storage.add_set(ts, "squat", 100)
    assert schedule.get_target_for_date(storage, day) == 1

    storage.add_set(ts, "pull-up", 5)
    storage.add_set(ts - timedelta(days=1), "pull-up", 20)
    assert schedule.get_target_for_date(storage, day + timedelta(days=1)) == 6
    assert schedule.get_target_for_date(storage, day + timedelta(days=2)) == 5
    assert schedule.get_target_for_date(storage, day + timedelta(days=4)) == 3
    assert schedule.get_target_for_date(storage, day + timedelta(days=20)) == 1
