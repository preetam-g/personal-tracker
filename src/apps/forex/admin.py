from django.contrib import admin

from apps.forex.models import Currency, ExchangeRate


class CurrencyAdmin(admin.ModelAdmin):

    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)


class ExchangeRateAdmin(admin.ModelAdmin):

    list_display = ('base_currency', 'target_currency', 'rate', 'fetched_at')
    search_fields = ('base_currency__code', 'target_currency__code')
    ordering = ('base_currency__code', 'target_currency__code', '-fetched_at')

admin.site.register(Currency, CurrencyAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)