from django.db import models
from django.db.models import Q, Max, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from datetime import timedelta, date as datetime_date

from apps.base.utils import TimeFrame
from apps.habits.utils import dates_between


class HabitQuerySet(models.QuerySet):

    def for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_active=True)


class HabitPlanQuerySet(models.QuerySet):

    def with_habit(self):
        return self.select_related('habit')

    def for_user(self, user):
        return self.filter(habit__user=user)

    def active_on(self, date):
        return self.filter(
            start_date__lte=date,
        ).filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=date)
        )

    def ensure_progress_until(self, date):
        from .models import DailyProgress

        date = min(date, timezone.localdate())

        plans = (
            self
            .filter(start_date__lte=date)
            .annotate(
                latest_progress_date=Max("daily_progress__date")
            )
        )

        rows = []
        for plan in plans:

            end_date = min(
                date,
                plan.end_date or date,
            )

            start_date = (
                plan.latest_progress_date + timedelta(days=1)
                if plan.latest_progress_date
                else plan.start_date
            )

            rows.extend(
                DailyProgress(
                    plan=plan,
                    date=progress_date,
                )
                for progress_date in dates_between(start_date, end_date)
            )

        DailyProgress.objects.bulk_create(
            rows,
            ignore_conflicts=True,
        )


class DailyProgressQuerySet(models.QuerySet):

    def with_plan(self):
        return self.select_related('plan')

    def with_habit(self):
        return self.select_related('plan__habit')

    def for_user(self, user):
        return self.filter(plan__habit__user=user)

    def in_range(self, start, end):
        return self.filter(date__range=(start, end))

    def get_trend_data(self, timeframe):
        today = timezone.localdate()
        start_date = TimeFrame.get_start_date(today, timeframe)

        qs = self.in_range(start_date, today)

        if timeframe == TimeFrame.THIS_YEAR:
            stats = (
                qs.annotate(period=TruncMonth('date'))
                .values('period')
                .annotate(
                    total_habits=Count('id'),
                    completed_habits=Count('id', filter=Q(value__gte=models.F('plan__target_value')))
                )
                .order_by('period')
            )

            trend_dict = {
                item['period'].month: round((item['completed_habits'] / item['total_habits']) * 100)
                for item in stats if item['total_habits'] > 0
            }

            trend_data = [
                {
                    'date': datetime_date(today.year, month, 1).strftime("%b %Y"),
                    'completion_rate': trend_dict.get(month, None)
                }
                for month in range(1, today.month + 1)
            ]

        else:
            stats = qs.values('date').annotate(
                total_habits=Count('id'),
                completed_habits=Count('id', filter=Q(value__gte=models.F('plan__target_value')))
            )

            trend_dict = {
                item['date']: round((item['completed_habits'] / item['total_habits']) * 100)
                for item in stats if item['total_habits'] > 0
            }

            trend_data = [
                {
                    'date': d.strftime('%b %d'),
                    'completion_rate': trend_dict.get(d, None)
                }
                for d in dates_between(start_date, today)
            ]

        return {
            'trend_data': trend_data,
            'start_date': start_date.isoformat(),
            'end_date': today.isoformat(),
            'timeframe': timeframe,
        }