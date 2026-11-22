import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


def test_storage_load_and_write(tmp_path: Path, data_dir: Path) -> None:
    from pull_up.database import Entry, Storage

    # Copy the data file to the temporary path
    shutil.copy(data_dir / "pull_ups.csv", tmp_path / "pull_ups.csv")

    storage = Storage(tmp_path / "pull_ups.csv")
    assert storage.data == [
        Entry(ts=datetime.fromisoformat("2025-11-21 22:30:00+00:00"), count=9),
        Entry(ts=datetime.fromisoformat("2025-11-22 19:43:21.686107+00:00"), count=10),
        Entry(ts=datetime.fromisoformat("2025-11-24 14:59:47.983597+00:00"), count=10),
    ]

    # Write the data back to the file
    storage.write()
    assert (tmp_path / "pull_ups.csv").read_text() == (data_dir / "pull_ups.csv").read_text()


def test_storage(tmp_path: Path) -> None:
    from pull_up.database import Entry, Storage

    # Storage is empty
    storage = Storage(tmp_path / "pull_ups.csv")
    assert storage.data == []
    assert storage.get_last_pull_up() is None
    assert storage.max_count is None
    assert storage.did_pull_ups(datetime.now(tz=UTC)) is False
    assert storage.pull_ups_for_date(datetime.now(tz=UTC)) == 1

    # Add one
    storage.add_pull_ups(ts1 := datetime.now(tz=UTC), 1)
    assert storage.get_last_pull_up() == Entry(ts=ts1, count=1)
    assert storage.max_count == 1
    assert storage.did_pull_ups(ts1) is True
    with pytest.raises(ValueError, match=r"Pull ups already recorded for this date"):
        storage.pull_ups_for_date(datetime.now(tz=UTC))
    assert storage.pull_ups_for_date(datetime.now(tz=UTC) + timedelta(days=1)) == 2

    # Add another
    storage.add_pull_ups(ts2 := datetime.now(tz=UTC), 2)
    assert storage.get_last_pull_up() == Entry(ts=ts2, count=2)
    assert storage.max_count == 2
    assert storage.did_pull_ups(ts2) is True
    assert storage.pull_ups_for_date(datetime.now(tz=UTC) + timedelta(days=1)) == 3
