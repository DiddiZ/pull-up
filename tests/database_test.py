import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


def test_storage_load_and_write(tmp_path: Path, data_dir: Path) -> None:
    from pull_up.database import ExerciseSet, Storage

    # Copy the data file to the temporary path
    shutil.copy(data_dir / "pull_ups.csv", tmp_path / "pull_ups.csv")

    storage = Storage(tmp_path / "pull_ups.csv")
    assert storage.data == [
        ExerciseSet(ts=datetime.fromisoformat("2025-11-21 22:30:00+00:00"), exercise="pull-up", count=9),
        ExerciseSet(ts=datetime.fromisoformat("2025-11-22 19:43:21.686107+00:00"), exercise="pull-up", count=10),
        ExerciseSet(ts=datetime.fromisoformat("2025-11-24 14:59:47.983597+00:00"), exercise="pull-up", count=10),
    ]

    # Write the data back to the file
    storage.write()
    assert (tmp_path / "pull_ups.csv").read_text() == (data_dir / "pull_ups.csv").read_text()


def test_storage(tmp_path: Path) -> None:
    from pull_up.database import ExerciseSet, Storage

    # Storage is empty
    storage = Storage(tmp_path / "pull_ups.csv")
    assert storage.data == []
    assert storage.get_last_set("pull-up") is None
    assert storage.get_max_count("pull-up") is None
    assert storage.did_exercise(datetime.now(tz=UTC), "pull-up") is False
    assert storage.pull_ups_for_date(datetime.now(tz=UTC)) == 1

    # Add one
    storage.add_set(ts1 := datetime.now(tz=UTC), "pull-up", 1)
    assert storage.get_last_set("pull-up") == ExerciseSet(ts=ts1, exercise="pull-up", count=1)
    assert storage.get_max_count("pull-up") == 1
    assert storage.did_exercise(ts1, "pull-up") is True
    with pytest.raises(ValueError, match=r"Pull ups already recorded for this date"):
        storage.pull_ups_for_date(datetime.now(tz=UTC))
    assert storage.pull_ups_for_date(datetime.now(tz=UTC) + timedelta(days=1)) == 2

    # Add another
    storage.add_set(ts2 := datetime.now(tz=UTC), "pull-up", 2)
    assert storage.get_last_set("pull-up") == ExerciseSet(ts=ts2, exercise="pull-up", count=2)
    assert storage.get_max_count("pull-up") == 2
    assert storage.did_exercise(ts2, "pull-up") is True
    assert storage.pull_ups_for_date(datetime.now(tz=UTC) + timedelta(days=1)) == 3
