from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

from apps.base.models import TimeStampedModel
from apps.forex.models import Currency


class UserProfile(AbstractUser):

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.username


class UserPreference(models.Model):
    """
    Preferences and custom settings for users. Rows are populated using signals whenever a new user is created.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences',
    )

    preferred_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='preferred_by_users',
    )
    show_advanced_currency_features = models.BooleanField(default=True)

    # app wise preferences
    accounts_preferences = models.JSONField(default=dict, blank=True)
    expenses_preferences = models.JSONField(default=dict, blank=True)
    ledger_preferences = models.JSONField(default=dict, blank=True)
    habits_preferences = models.JSONField(default=dict, blank=True)


    def __str__(self):
        return f"{self.user} preferences"

    def _set_preferences(self, field_name: str, **kwargs):
        preferences = getattr(self, field_name)
        preferences.update(kwargs)

        setattr(self, field_name, preferences)
        self.save(update_fields=[field_name])

    def _get_preference(self, field_name: str, key, default=None):
        return getattr(self, field_name).get(key, default)


    # expenses
    def set_expenses_preferences(self, **kwargs):
        self._set_preferences('expenses_preferences', **kwargs)

    def get_expenses_preferences(self, key, default=None):
        return self._get_preference(
            'expenses_preferences',
            key,
            default,
        )


    # ledger
    def set_ledger_preferences(self, **kwargs):
        self._set_preferences('ledger_preferences', **kwargs)

    def get_ledger_preferences(self, key, default=None):
        return self._get_preference(
            'ledger_preferences',
            key,
            default,
        )


    # accounts
    def set_accounts_preferences(self, **kwargs):
        self._set_preferences('accounts_preferences', **kwargs)

    def get_accounts_preferences(self, key, default=None):
        return self._get_preference(
            'accounts_preferences',
            key,
            default,
        )


    # habits
    def set_habits_preferences(self, **kwargs):
        self._set_preferences('habits_preferences', **kwargs)

    def get_habits_preferences(self, key, default=None):
        return self._get_preference(
            'habits_preferences',
            key,
            default,
        )


    def set_forex_preferences(
            self,
            preferred_currency: Currency | None = None,
            show_advanced_currency_features: bool | None = None
    ):
        update_fields = []

        if preferred_currency is not None:
            self.preferred_currency = preferred_currency
            update_fields.append('preferred_currency')

        if show_advanced_currency_features is not None:
            self.show_advanced_currency_features = (
                show_advanced_currency_features
            )
            update_fields.append(
                'show_advanced_currency_features'
            )

        if update_fields:
            self.save(update_fields=update_fields)