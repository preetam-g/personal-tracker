from django.db import models
from django.db.models import Sum, Min, Max
from django.db.models.functions import TruncDate
from django.utils import timezone

class ExpenseManager(models.Manager):

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().select_related('category', 'type')

    def all_for_user(self, user) -> models.QuerySet:
        return self.get_queryset().filter(user=user)

    def filtered_for_user(self, user, filter_form) -> models.QuerySet:
        qs = self.all_for_user(user)

        field_mapping = {
            'keyword': 'description__icontains',
            'start_date': 'date__gte',
            'end_date': 'date__lte',
            'category': 'category',
            'type': 'type',
        }

        filters = {field_mapping[k]: v for k, v in filter_form.items() if v and (k in field_mapping)}
        qs = qs.filter(**filters)

        return qs.order_by(filter_form.get('sort_by') or '-date')

    def get_stats(self, user, filter_form) -> dict:

        qs = self.filtered_for_user(user, filter_form)

        daily_stats = qs.annotate(
            day=TruncDate('date'),
        ).values('day').annotate(
            total_spent=Sum('amount'),
        ).order_by(filter_form.get('sort_by') or '-day')

        total = sum(item['total_spent'] for item in daily_stats)

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