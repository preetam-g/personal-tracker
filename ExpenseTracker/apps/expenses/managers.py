from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Sum, Min, Max
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .utils import TimeFrame, get_start_date, get_grouped_data
from apps.base.models import SoftDeleteQuerySet, SoftDeleteManager


class ExpenseManager(SoftDeleteManager):

    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().select_related('category', 'type')

    def all_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.get_queryset().filter(user=user)

    def filtered_for_user(self, user:AbstractBaseUser, filter_form:dict) -> SoftDeleteQuerySet:
        qs = self.all_for_user(user)

        field_mapping = {
            'keyword': 'note__icontains',
            'start_date': 'date__gte',
            'end_date': 'date__lte',
            'category': 'category',
            'type': 'type',
        }

        filters = {field_mapping[k]: v for k, v in filter_form.items() if v and (k in field_mapping)}
        qs = qs.filter(**filters)

        return qs.order_by(filter_form.get('sort_by') or '-date')

    def get_stats(self, user:AbstractBaseUser, filter_form:dict) -> dict:

        qs = self.filtered_for_user(user, filter_form)

        daily_stats = qs.annotate(
            day=TruncDate('date'),
        ).values('day').annotate(
            total_spent=Sum('amount'),
        ).order_by(filter_form.get('sort_by') or '-day')

        total = sum(item['total_spent'] for item in daily_stats) or 0.0

        end = filter_form.get('end_date')
        if not end:
            latest_record = qs.aggregate(last_date=Max('date'))['last_date']
            end = latest_record.date() if latest_record else timezone.now().date()

        start = filter_form.get('start_date')
        if not start:
            earliest_record = qs.aggregate(first_date=Min('date'))['first_date']
            start = earliest_record.date() if earliest_record else end

        no_of_days = (end - start).days + 1
        daily_avg = total / no_of_days
        return {
            'total': total,
            'daily': daily_avg,
            'weekly': daily_avg * 7,
            'no_of_days': no_of_days,
        }

    def get_dashboard_data(self, user: AbstractBaseUser, timeFrame: str = TimeFrame.THIS_MONTH) -> dict:
        qs = self.all_for_user(user)
        today = timezone.now().date()

        start_date = get_start_date(today, timeFrame)

        qs = qs.filter(date__date__gte=start_date, date__date__lte=today)

        period_total = qs.aggregate(total=Sum('amount'))['total'] or 0.0

        category_totals = get_grouped_data(qs, 'category__name')
        type_totals = get_grouped_data(qs, 'type__name')

        if timeFrame == TimeFrame.THIS_YEAR:
            trend_qs = qs.annotate(period=TruncMonth('date')) \
                .values_list('period') \
                .annotate(total=Sum('amount')) \
                .order_by('period')

            trend_data = [
                {'date': p.strftime("%b %Y"), 'total': float(t)}
                for p, t in trend_qs if p
            ]

        else:
            trend_qs = qs.annotate(period=TruncDate('date')) \
                .values_list('period') \
                .annotate(total=Sum('amount')) \
                .order_by('period')

            trend_dict = {p: float(t) for p, t in trend_qs if p}

            delta_days = (today - start_date).days
            trend_data = [
                {
                    'date': (start_date + timedelta(days=i)).strftime('%b %d'),
                    'total': trend_dict.get(start_date + timedelta(days=i), 0.0)
                }
                for i in range(delta_days + 1)
            ]

        return {
            'period_total': float(period_total),
            'category_data': category_totals,
            'type_data': type_totals,
            'trend_data': trend_data,
            'current_timeframe': timeFrame,
        }