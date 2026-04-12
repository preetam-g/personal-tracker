from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Sum, Min, Max, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime, time
from .utils import TimeFrame, get_start_date, get_grouped_data
from apps.base.models import SoftDeleteQuerySet, SoftDeleteManager, SoftDeleteModel


class ExpenseManager(SoftDeleteManager):

    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().select_related('category', 'type')

    def all_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.get_queryset().filter(user=user)

    def filtered_for_user(self, user:AbstractBaseUser, filter_form:dict) -> SoftDeleteQuerySet:
        qs = self.all_for_user(user)

        field_mapping = {
            'start_date': 'date__gte',
            'category': 'category',
            'type': 'type',
        }

        start_date = filter_form.get('start_date')
        if start_date:
            start_date = timezone.make_aware(datetime.combine(start_date, time.min))
            filter_form.update(start_date=start_date)

        filters = {field_mapping[k]: v for k, v in filter_form.items() if v and (k in field_mapping)}
        qs = qs.filter(**filters)

        end_date = filter_form.get('end_date')
        if end_date:
            end_date = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
            qs = qs.filter(date__lt=end_date)

        if filter_form.get('sort_by'):
            qs = qs.order_by(filter_form.get('sort_by'))

        return qs

    def get_stats(self, user:AbstractBaseUser, filter_form:dict) -> dict:

        qs = self.filtered_for_user(user, filter_form).order_by()

        metrics = qs.aggregate(
            total=Sum('amount'),
            first_date=Min('date'),
            last_date=Max('date'),
        )

        db_first = metrics['first_date']
        db_last = metrics['last_date']
        db_start_date = timezone.localdate(db_first) if db_first else None
        db_end_date = timezone.localdate(db_last) if db_last else None

        total = metrics['total'] or 0.0
        start = filter_form.get('start_date') or db_start_date
        end = filter_form.get('end_date') or db_end_date

        if (not start) or (not end):
            return {
                'total': 0.0,
                'daily': 0.0,
                'weekly': 0.0,
                'no_of_days': 0,
                'start_date': start,
                'end_date': end,
            }

        if isinstance(start, datetime): start = start.date()
        if isinstance(end, datetime): end = end.date()

        no_of_days = max((end - start).days + 1, 1)
        daily_avg = total / no_of_days
        return {
            'total': total,
            'daily': daily_avg,
            'weekly': daily_avg * 7,
            'no_of_days': no_of_days,
            'start_date': start,
            'end_date': end,
        }

    def get_dashboard_data(self, user:AbstractBaseUser, timeFrame: str) -> dict:

        today = timezone.localdate()

        start_date = get_start_date(today, timeFrame)
        qs = self.filtered_for_user(
            user=user,
            filter_form={
                'start_date': start_date,
                'end_date': today,
            }
        )

        period_total = qs.aggregate(total=Sum('amount'))['total'] or 0.0
        category_totals = get_grouped_data(qs, 'category__name')
        type_totals = get_grouped_data(qs, 'type__name')

        if timeFrame == TimeFrame.THIS_YEAR:
            trend_qs = (
                qs.annotate(period=TruncMonth('date'))
                .values('period')
                .annotate(total=Sum('amount'))
                .order_by('period')
            )

            trend_data = [
                {'date': item['period'].strftime("%b %Y"), 'total': float(item['total'])}
                for item in trend_qs if item['period']
            ]
        else:
            trend_qs = (
                qs.annotate(period=TruncDate('date'))
                .values('period')
                .annotate(total=Sum('amount'))
                .order_by('period')
            )

            trend_dict = {item['period']: float(item['total']) for item in trend_qs if item['period']}

            delta_days = (today - start_date).days
            trend_data = [
                {
                    'date': (start_date + timedelta(days=i)).strftime('%b %d'),
                    'total': trend_dict.get(start_date + timedelta(days=i), 0.0)
                }
                for i in range(delta_days + 1)
            ] # this is to ensure that there are no missing dates

        return {
            'period_total': period_total,
            'category_data': category_totals,
            'type_data': type_totals,
            'trend_data': trend_data,
            'current_timeframe': timeFrame,
        }


class CategoryTypeManager(SoftDeleteManager):

    def user_items(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return super().get_queryset().filter(
            Q(user=user) | Q(user__isnull=True),
        )