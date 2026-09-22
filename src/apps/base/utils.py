from django.db import models
import datetime
from django import forms


class TimeFrame(models.TextChoices):
    SEVEN_DAYS = '7_days', 'Last 7 Days'
    THIRTY_DAYS = '30_days', 'Last 30 Days'
    THIS_MONTH = 'this_month', 'This month'
    THIS_YEAR = 'this_year', 'This year'

    @classmethod
    def get_start_date(cls, today: datetime.date, timeframe) -> datetime.date:
        """
        Returns the start date for the selected timeframe.
        The range is inclusive of today.
        """
        date_mapping = {
            cls.SEVEN_DAYS: lambda t: t - datetime.timedelta(days=6),
            cls.THIRTY_DAYS: lambda t: t - datetime.timedelta(days=29),
            cls.THIS_MONTH: lambda t: t.replace(day=1),
            cls.THIS_YEAR: lambda t: t.replace(day=1, month=1),
        }
        calculation_func = date_mapping.get(timeframe)

        return calculation_func(today) if timeframe else None


DEFAULT_BASE_CURRENCY_CODE = 'INR'
DEFAULT_BASE_CURRENCY_SYMBOL = '₹'


class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, *args, empty_label="---------", **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_label = empty_label
        self.choices = [("", empty_label), *self.choices]