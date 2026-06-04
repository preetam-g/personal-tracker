from django.db.models import Sum
from django.db import models


class SortChoices(models.TextChoices):
    NEWEST_FIRST = '-date', 'Newest First'
    OLDEST_FIRST =  'date', 'Oldest First'
    HIGHEST_AMOUNT = '-amount', 'Highest Amount'
    LOWEST_AMOUNT = 'amount', 'Lowest Amount'


def get_grouped_data(qs: models.QuerySet, field: str) -> dict:
    data = list(
        qs.values(field)
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    return {
        'labels': [item[field] or 'Others' for item in data],
        'data': [round(float(item['total'] or 0.0), 2) for item in data],
    }