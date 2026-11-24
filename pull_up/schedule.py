from abc import ABC, abstractmethod
from datetime import date
from typing import override

from pull_up.database import Storage


class ExerciseSchedule(ABC):
    """Interface for exercise schedules."""

    @abstractmethod
    def get_target_for_date(self, storage: Storage, date: date) -> int:
        """Calculate the target for a given date."""


class IncrementingExerciseSchedule(ExerciseSchedule):
    """Incrementing exercise schedule based on past performance."""

    def __init__(self, exercise: str, *, increment: int = 1, decrement: int = 1, initial_target: int = 1) -> None:
        """Initialize the exercise schedule."""
        self.exercise = exercise
        self.increment = increment
        self.decrement = decrement
        self.initial_target = initial_target

    @override
    def get_target_for_date(self, storage: Storage, date: date) -> int:
        """Calculate the target for a given date."""
        last = storage.get_last_set(self.exercise, before=date)
        if last is None:  # Initial target if no previous sets exist
            return self.initial_target

        days_passed = (date - last.ts.date()).days
        return max(last.count + self.increment - self.decrement * (days_passed - 1), self.initial_target)
