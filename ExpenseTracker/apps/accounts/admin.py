from django.contrib import admin
from .models import UserProfile, UserPreference
from apps.base.admin import SoftDeleteAdmin


class UserProfileAdmin(SoftDeleteAdmin):

    list_display = ['username', 'first_name', 'last_name', 'email']
    search_fields = ['username', 'email']
    list_filter = ['username']


class UserPreferenceAdmin(SoftDeleteAdmin):

    list_display = [
        'user',
        'base_currency',
        'show_forex_features',
        'accounts_preferences',
        'expenses_preferences',
        'ledger_preferences',
        'ui_preferences',
    ]

    class Meta:
        ordering = ['user']

    @admin.display(description='Forex Features')
    def show_forex_features(self, obj):
        return obj.show_advanced_currency_features

    @admin.display(description='Base Currency')
    def base_currency(self, obj):
        return obj.preferred_currency


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserPreference, UserPreferenceAdmin)