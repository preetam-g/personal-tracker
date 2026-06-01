from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

from apps.base.models import SoftDeleteModel
from apps.forex.models import Currency


class UserProfile(AbstractUser, SoftDeleteModel):
    SOFT_DELETE_CASCADES = (
        'expenses',
        'expensecategory_items',
        'expensetype_items',
        'transactions',
        'contacts',
        'preferences',
    )

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.username


class UserPreference(SoftDeleteModel):
    """
    Preferences and custom settings for users. Rows are populated using signals ( in accounts/signals.py ) whenever a new user is created.
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

    ui_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user} preferences"


    def set_expenses_preferences(self, **kwargs):
        self.expenses_preferences.update(kwargs)
        self.save(update_fields=['expenses_preferences'])

    def get_expenses_preferences(self, key, default=None):
        return self.expenses_preferences.get(key, default)


    def set_ledger_preferences(self, **kwargs):
        self.ledger_preferences.update(kwargs)
        self.save(update_fields=['ledger_preferences'])

    def get_ledger_preferences(self, key, default=None):
        return self.ledger_preferences.get(key, default)


    def set_accounts_preferences(self, **kwargs):
        self.accounts_preferences.update(kwargs)
        self.save(update_fields=['accounts_preferences'])

    def get_accounts_preferences(self, key, default=None):
        return self.accounts_preferences.get(key, default)


    def set_ui_preferences(self, **kwargs):
        self.ui_preferences.update(kwargs)
        self.save(update_fields=['ui_preferences'])

    def get_ui_preferences(self, key, default=None):
        return self.ui_preferences.get(key, default)
