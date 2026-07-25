"""
Habit Tracker Models

The habit tracker is designed around four models:

Habit
    Permanent habit library owned by a user.

HabitPlan
    Represents a period during which a Habit is actively tracked.

    Stores the configuration used during that period, such as the
    daily target and unit.

    A Habit can have multiple HabitPlans over time, allowing the user
    to stop tracking it, restart it later, or change how it is tracked
    without modifying historical data.

DailyProgress
    Stores the actual progress made for one HabitPlan on one day.

Relationship diagram
        User
        ▼
        Habit
        ▼
        WeeklyGoal
        ▼
        DailyProgress

Example

    Habit
        Water

        HabitPlan
            Jul 1 -> Jul 20
            8 glasses/day

        HabitPlan
            Aug 5 -> NULL
            4 litres/day

NULL end_date means the HabitPlan is currently active.
"""

from django.db import models
from django.db.models.functions import Lower
from django.conf import settings

from apps.base.models import TimeStampedModel


class Habit(TimeStampedModel):
    """
        Permanent habit owned by a user.
        This model stores the DEFAULT configuration used whenever a new Goal is created.
        Editing this model only affects future weeks.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
    )

    name = models.CharField(max_length=100)

    default_target_value = models.PositiveIntegerField(default=1)

    unit = models.CharField(
        max_length=50,
        default='times',
        help_text='Display unit (glasses, tablets, pages, minutes...)',
    )

    class Meta:
        ordering = ['name']

        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'user',
                name="unique_habit_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(default_target_value__gt=0),
                name="habit_default_target_positive",
            ),
        ]

    def __str__(self):
        return self.name


class HabitPlan(TimeStampedModel):
    """
        A period during which a Habit is actively tracked.
        start_date and end_date are inclusive.
        An end_date of NULL means the plan is currently active.
        Example:
            Water
            start_date   = 2026-07-20
            end_date     = 2026-07-25
            target_value = 8
            unit         = "glasses"
        means Water was tracked from July 20 through July 25, with a daily target of 8 glasses.
        If the user starts tracking Water again later, a new HabitPlan is
        created rather than modifying this historical plan.
    """
    habit = models.ForeignKey(
        Habit,
        on_delete=models.PROTECT,
        related_name='plans',
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    target_value = models.PositiveIntegerField()
    unit = models.CharField(
        max_length=50,
        help_text='Display unit for this tracking period. (glasses, tablets, pages, minutes...)',
    )

    class Meta:
        ordering = ["-start_date", "-id"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_value__gt=0),
                name="habit_plan_target_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(end_date__isnull=True)
                    | models.Q(end_date__gte=models.F("start_date"))
                ),
                name="habit_plan_valid_date_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.habit.name} ({self.start_date})"

    def applies_on(self, date) -> bool:
        """
            Return whether this plan applies on the given date.
            Both start_date and end_date are inclusive.
        """
        return (
            self.start_date <= date
            and (
                self.end_date is None
                or date <= self.end_date
            )
        )


class DailyProgress(TimeStampedModel):
    """
        Progress for one HabitPlan on one calendar day.
        The target and unit for the progress are determined by the
        associated HabitPlan.
        Example:
            HabitPlan:
                Water
                target_value = 8
                unit = "glasses"
            DailyProgress:
                date = 2026-07-25
                value = 6
            Result:
                6 / 8 glasses
        A missing DailyProgress row can be treated as zero progress.
        Therefore, rows do not need to be created in advance for every
        day that a HabitPlan is active.
    """

    plan = models.ForeignKey(
        HabitPlan,
        on_delete=models.CASCADE,
        related_name='daily_progress',
    )

    date = models.DateField()

    value = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date"]

        constraints = [
            models.UniqueConstraint(
                fields=('plan', 'date'),
                name="unique_daily_progress_per_plan",
            ),
        ]

    def __str__(self):
        return f"{self.plan.habit.name} - {self.date}"

    @property
    def completed(self) -> bool:
        """Return whether the daily target has been reached."""
        return self.value >= self.plan.target_value

    @property
    def percentage(self) -> int:
        """Return completion percentage"""
        return min(
            100,
            round(100 * self.value / self.plan.target_value),
        )

    @property
    def remaining(self) -> int:
        """Remaining value required to complete today's goal."""
        return max(
            0,
            self.plan.target_value - self.value,
        )

    @property
    def overflow(self) -> int:
        """Amount completed beyond today's target."""
        return max(
            0,
            self.value - self.plan.target_value,
        )