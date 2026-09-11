from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.conf import settings
from django.utils import timezone

from apps.base.models import TimeStampedModel
from .managers import HabitQuerySet, HabitPlanQuerySet, DailyProgressQuerySet
from .utils import HabitPlanStatus


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

    default_unit = models.CharField(
        max_length=50,
        default='times',
        help_text='Display unit (glasses, tablets, pages, minutes...)',
    )

    is_active = models.BooleanField(default=True)

    objects = HabitQuerySet.as_manager()
    class Meta:
        ordering = ['-is_active', 'name']

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

    @property
    def target_str(self):
        return f"{self.default_target_value} {self.default_unit}"


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
    unit = models.CharField(max_length=50)

    objects = HabitPlanQuerySet.as_manager()
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
        end = self.end_date or "Ongoing"
        return f"{self.habit} - {self.target_str} ({self.start_date} → {end})"

    @property
    def status(self):

        today = timezone.localdate()
        if self.start_date > today:
            return HabitPlanStatus.UPCOMING
        elif self.end_date and self.end_date < today:
            return HabitPlanStatus.ENDED

        return HabitPlanStatus.ACTIVE

    @property
    def is_upcoming(self):
        return self.status == HabitPlanStatus.UPCOMING

    @property
    def is_active(self):
        return self.status == HabitPlanStatus.ACTIVE

    @property
    def is_ended(self):
        return self.status == HabitPlanStatus.ENDED

    @property
    def target_str(self):
        return f"{self.target_value} {self.unit}"

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

    def clean(self):
        super().clean()

        overlapping_plans = HabitPlan.objects.filter(
            habit=self.habit,
        ).exclude(pk=self.pk)

        if self.end_date:
            overlapping_plans = overlapping_plans.filter(
                start_date__lte=self.end_date,
            )

        overlapping_plans = overlapping_plans.filter(
            models.Q(end_date__isnull=True)
            | models.Q(end_date__gte=self.start_date)
        )

        if overlapping_plans.exists():
            raise ValidationError(
                f"{self.habit} already has a goal during this period. "
                "Choose dates that don't overlap with the existing goal."
            )


class DailyProgress(TimeStampedModel):
    """
        Progress for one HabitPlan on one calendar day.

        A DailyProgress row is maintained for each elapsed day covered by
        the HabitPlan. Future progress rows are not created.

        The target and unit are determined by the associated HabitPlan.
    """

    plan = models.ForeignKey(
        HabitPlan,
        on_delete=models.CASCADE,
        related_name='daily_progress',
    )
    date = models.DateField()
    value = models.PositiveIntegerField(default=0)

    objects = DailyProgressQuerySet.as_manager()
    class Meta:
        ordering = ["-date", "-id"]

        constraints = [
            models.UniqueConstraint(
                fields=('plan', 'date'),
                name="unique_daily_progress_per_plan",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.plan.habit} - {self.date}"

    @property
    def completed(self) -> bool:
        """Return whether the daily target has been reached."""
        return self.value >= self.plan.target_value

    @property
    def progress_str(self):
        return f"{self.value}/{self.plan.target_value} {self.plan.unit}"

    @property
    def percentage(self) -> int:
        """Return completion percentage ( can exceed 100 )"""
        return round(100 * self.value / self.plan.target_value)

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

    def clean(self):
        super().clean()

        if self.plan_id and not self.plan.applies_on(self.date):
            raise ValidationError({
                "date": "Progress date must fall within the plan's date range."
            })