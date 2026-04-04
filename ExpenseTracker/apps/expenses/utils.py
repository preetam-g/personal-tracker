from django.db.models import Sum
from django.db import models
import datetime

class SortChoices(models.TextChoices):
    NEWEST_FIRST = '-date', 'Newest First'
    OLDEST_FIRST =  'date', 'Oldest First'
    HIGHEST_AMOUNT = '-amount', 'Highest Amount'
    LOWEST_AMOUNT = 'amount', 'Lowest Amount'


class TimeFrame(models.TextChoices):
    SEVEN_DAYS = '7_days', 'Last 7 Days'
    THIS_MONTH = 'this_month', 'This month'
    THIS_YEAR = 'this_year', 'This year'


def get_start_date(today: datetime.date, timeFrame: str) -> datetime.date:
    """
    Takes a pure calendar date and returns the starting calendar date.
    """

    mapping = {
        TimeFrame.SEVEN_DAYS: lambda d: d - datetime.timedelta(days=6),
        TimeFrame.THIS_MONTH: lambda d: d.replace(day=1),
        TimeFrame.THIS_YEAR: lambda d: d.replace(month=1, day=1),
    }

    # Default to THIS_MONTH if an unknown timeframe is passed
    return mapping.get(timeFrame)(today)


def get_grouped_data(qs: models.QuerySet, field: str) -> dict:
    data = list(
        qs.values(field)
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    return {
        'labels': [item[field] or 'Others' for item in data],
        'data': [float(item['total'] or 0.0) for item in data],
    }

