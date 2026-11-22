import csv
from datetime import datetime
from pathlib import Path

from pydantic import AwareDatetime, BaseModel


class Entry(BaseModel, extra="forbid"):
    """A single pull up entry."""

    ts: AwareDatetime
    count: int


class Storage:
    """Simple CSV data storage."""

    def __init__(self, file: Path) -> None:
        """Initialize storage from a CSV file."""
        self.file = file
        self.data: list[Entry] = []
        if file.exists():
            with open(file) as f:
                self.data = [Entry.model_validate(row) for row in csv.DictReader(f)]

    def add_pull_ups(self, ts: datetime, count: int) -> None:
        """Add a new pull up entry."""
        self.data.append(Entry(ts=ts, count=count))

    def write(self) -> None:
        """Write data back to CSV file."""
        with open(self.file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["ts", "count"])
            writer.writeheader()
            for entry in self.data:
                writer.writerow(entry.model_dump())

    def did_pull_ups(self, ts: datetime) -> bool:
        """Check if pull ups were done on a given date."""
        return any(entry.ts.date() == ts.date() for entry in self.data)

    def get_last_pull_up(self) -> Entry | None:
        """Get the last pull up entry."""
        return max(self.data, key=lambda e: e.ts, default=None)

    def pull_ups_for_date(self, date: datetime) -> int:
        """Calculate pull up target for a given date."""
        last = self.get_last_pull_up()
        if last is None:
            return 1

        if last.ts.date() >= date.date():
            raise ValueError("Pull ups already recorded for this date")

        days_passed = (date.date() - last.ts.date()).days
        return max(last.count + 1 - (days_passed - 1), 1)

    @property
    def max_count(self) -> int | None:
        """The maximum pull up count recorded."""
        return max((entry.count for entry in self.data), default=None)
