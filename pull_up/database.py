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

    def get_sets(
        self, *, exercise: str | None = None, day: date | None = None, before: date | None = None
    ) -> Iterator[ExerciseSet]:
        """Filter entries by exercise type."""
        for entry in self.data:
            if exercise is not None and entry.exercise != exercise:
                continue
            if day is not None and entry.ts.date() != day:
                continue
            if before is not None and entry.ts.date() >= before:
                continue
            yield entry

    def get_last_set(self, exercise: str, *, before: date | None = None) -> ExerciseSet | None:
        """Get the last exercise set for a given exercise."""
        return max(self.get_sets(exercise=exercise, before=before), key=lambda e: e.ts, default=None)

    def get_max_count(self, exercise: str, *, day: date | None = None) -> int | None:
        """Get the maximum count recorded for a given exercise."""
        return max((entry.count for entry in self.get_sets(exercise=exercise, day=day)), default=None)
