"""
Habit Tracker Models

The habit tracker is designed around four models:

Habit
    Permanent habit library owned by a user.

WeeklyPlan
    Represents a single ISO week for a user.

WeeklyGoal
    A snapshot of a Habit for a specific WeeklyPlan.
    Stores week-specific settings (target, unit, order, etc.)
    So, history never changes when the Habit is edited.

DailyProgress
    Stores the actual progress made for one WeeklyGoal on one day.

Relationship diagram

              User
            ▼     ▼
         Habit   WeeklyPlan
             ▼    ▼
            WeeklyGoal
                ▼
          DailyProgress
"""

from django.db import models
from django.db.models.functions import Lower
from django.conf import settings

from apps.base.models import TimeStampedModel


class Habit(TimeStampedModel):
    """
        Permanent habit owned by a user.

        Think of this as the user's habit library.

        This model stores the DEFAULT configuration used whenever a new WeeklyGoal is created.

        Editing this model only affects future weeks.
        Existing WeeklyGoals remain unchanged.
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


class WeeklyPlan(TimeStampedModel):
    """
        Represents one ISO week.
        Example: User Week 31
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weekly_plans',
    )

    week_start = models.DateField()
    iso_year = models.PositiveSmallIntegerField()
    iso_week = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["-week_start"]

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'iso_year', 'iso_week'),
                name="unique_weekly_plan_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(iso_week__gte=1, iso_week__lte=53),
                name="weekly_plan_valid_iso_week",
            ),
        ]

    def __str__(self):
        return f'Week {self.iso_week}-{self.iso_year}'


class WeeklyGoal(TimeStampedModel):
    """
        Snapshot of a Habit for one week.
        Editing the Habit later will NOT affect this model.
    """

    plan = models.ForeignKey(
        WeeklyPlan,
        on_delete=models.CASCADE,
        related_name='goals',
    )

    habit = models.ForeignKey(
        Habit,
        on_delete=models.PROTECT,
        related_name='weekly_goals',
    )

    target_value = models.PositiveIntegerField()
    unit = models.CharField(max_length=50)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", 'id']

        constraints = [
            models.UniqueConstraint(
                fields=('plan', 'habit'),
                name="unique_weekly_goal_per_habit",
            ),
            models.CheckConstraint(
                condition=models.Q(target_value__gt=0),
                name="weekly_goal_target_positive",
            ),
        ]

    def __str__(self):
        return f'{self.habit.name} ({self.plan})'


class DailyProgress(TimeStampedModel):
    """
        Progress for one WeeklyGoal on one day.

        Exactly one row exists for every
        (WeeklyGoal, Date) combination.
    """

    goal = models.ForeignKey(
        WeeklyGoal,
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
                fields=('goal', 'date'),
                name="unique_daily_progress_per_goal",
            ),
        ]

    def __str__(self):
        return f"{self.goal.habit.name} - {self.date}"

    @property
    def completed(self) -> bool:
        """Returns True if the goal has been completed for the day."""
        return self.value >= self.goal.target_value

    @property
    def percentage(self) -> float:
        """Completion percentage capped at 100."""
        return min(
            100.0,
            round(100.0 * self.value / self.goal.target_value, 2),
        )

    @property
    def remaining(self) -> int:
        """Remaining value required to complete today's goal."""
        return max(
            0,
            self.goal.target_value - self.value,
        )

    @property
    def overflow(self) -> int:
        """Amount completed beyond today's target."""
        return max(
            0,
            self.value - self.goal.target_value,
        )