from django.db import models
import datetime


class TimeFrame(models.TextChoices):
    SEVEN_DAYS = '7_days', 'Last 7 Days'
    THIRTY_DAYS = '30_days', 'Last 30 Days'
    THIS_MONTH = 'this_month', 'This month'
    THIS_YEAR = 'this_year', 'This year'

    @classmethod
    def get_start_date(cls, today: datetime.date, timeframe: str) -> datetime.date:
        """
        Returns the start date for the selected timeframe.
        The range is inclusive of today.
        """
        if timeframe == cls.SEVEN_DAYS:
            return today - datetime.timedelta(days=6)

        elif timeframe == cls.THIRTY_DAYS:
            return today - datetime.timedelta(days=29)

        elif timeframe == cls.THIS_MONTH:
            return today.replace(day=1)

        return today.replace(day=1, month=1)


DEFAULT_BASE_CURRENCY_CODE = 'INR'
DEFAULT_BASE_CURRENCY_SYMBOL = '₹'