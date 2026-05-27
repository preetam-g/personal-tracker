from django.db import models
import datetime


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


DEFAULT_BASE_CURRENCY_CODE = 'INR'
DEFAULT_BASE_CURRENCY_SYMBOL = '₹'