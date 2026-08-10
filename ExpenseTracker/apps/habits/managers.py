from django.db import models
from django.db.models import Q, Max, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from datetime import timedelta, date as datetime_date

from apps.base.utils import TimeFrame
from apps.habits.utils import dates_between, HabitPlanStatus


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

    def by_status(self, *statuses):
        """
        Filter HabitPlans by one or more HabitPlanStatus values.
        """
        if not statuses:
            return self.none()

        query = Q()
        for status in statuses:
            if isinstance(status, str):
                status = HabitPlanStatus(status)
            query |= status.query

        return self.filter(query)


class DailyProgressQuerySet(models.QuerySet):

    def with_plan(self):
        return self.select_related('plan')

    def with_habit(self):
        return self.select_related('plan__habit')

    def for_user(self, user):
        return self.filter(plan__habit__user=user)

    def in_range(self, start, end):
        return self.filter(date__range=(start, end))

    def get_trend_data(self, start_date, end_date):
        qs = self.in_range(start_date, end_date)

        delta_days = (end_date - start_date).days
        if delta_days > 60:
            stats = (
                qs.annotate(period=TruncMonth('date'))
                .values('period')
                .annotate(
                    total_habits=Count('id'),
                    completed_habits=Count('id', filter=Q(value__gte=models.F('plan__target_value')))
                )
            )

            trend_dict = {}
            for item in stats:
                if item['total_habits'] > 0 and item['period']:
                    period_date = item['period'].date() if hasattr(item['period'], 'date') else item['period']
                    trend_dict[period_date] = round((item['completed_habits'] / item['total_habits']) * 100)

            trend_data = []
            current_month = datetime_date(start_date.year, start_date.month, 1)
            end_month = datetime_date(end_date.year, end_date.month, 1)

            while current_month <= end_month:
                trend_data.append({
                    'date': current_month.strftime("%b %Y"),
                    'completion_rate': trend_dict.get(current_month, None)
                })
                if current_month.month == 12:
                    current_month = datetime_date(current_month.year + 1, 1, 1)
                else:
                    current_month = datetime_date(current_month.year, current_month.month + 1, 1)

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
                for d in dates_between(start_date, end_date)
            ]

        return {
            'trend_data': trend_data,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }