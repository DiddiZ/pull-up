import csv
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path

from pydantic import AwareDatetime, BaseModel


class ExerciseSet(BaseModel, extra="forbid"):
    """A single pull up entry."""

    ts: AwareDatetime
    exercise: str
    count: int


class Storage:
    """Simple CSV data storage."""

    def __init__(self, file: Path) -> None:
        """Initialize storage from a CSV file."""
        self.file = file
        self.data: list[ExerciseSet] = []
        if file.exists():
            with open(file) as f:
                self.data = [ExerciseSet.model_validate(row) for row in csv.DictReader(f)]

    def add_set(self, ts: datetime, exercise: str, count: int) -> None:
        """Add a new exercise set."""
        self.data.append(ExerciseSet(ts=ts, exercise=exercise, count=count))

    def write(self) -> None:
        """Write data back to CSV file."""
        with open(self.file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["ts", "exercise", "count"])
            writer.writeheader()
            for entry in self.data:
                writer.writerow(entry.model_dump())

    def get_sets(self, *, exercise: str | None = None, day: date | None = None) -> Iterator[ExerciseSet]:
        """Filter entries by exercise type."""
        for entry in self.data:
            if exercise is not None and entry.exercise != exercise:
                continue
            if day is not None and entry.ts.date() != day:
                continue
            yield entry

    def did_exercise(self, ts: datetime, exercise: str) -> bool:
        """Check if a specific exercise was done on a given date."""
        return any(self.get_sets(exercise=exercise, day=ts.date()))

    def get_last_set(self, exercise: str) -> ExerciseSet | None:
        """Get the last exercise set for a given exercise."""
        return max(self.get_sets(exercise=exercise), key=lambda e: e.ts, default=None)

    def pull_ups_for_date(self, date: datetime) -> int:
        """Calculate pull up target for a given date."""
        last = self.get_last_set("pull-up")
        if last is None:
            return 1

        if last.ts.date() >= date.date():
            raise ValueError("Pull ups already recorded for this date")

        days_passed = (date.date() - last.ts.date()).days
        return max(last.count + 1 - (days_passed - 1), 1)

    def get_max_count(self, exercise: str) -> int | None:
        """Get the maximum count recorded for a given exercise."""
        return max((entry.count for entry in self.get_sets(exercise=exercise)), default=None)
