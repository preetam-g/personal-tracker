from django.contrib import admin
from apps.base.admin import SoftDeleteAdmin
from apps.expenses.models import Expense, ExpenseCategory, ExpenseType
from django.utils import timezone

class ExpenseAdmin(SoftDeleteAdmin):

    list_display = ('formatted_date', 'amount', 'category', 'type', 'user')
    list_filter =  ('category', 'type')

    @admin.display(description='Date', ordering='-date')
    def formatted_date(self, obj):
        return timezone.localtime(obj.date).strftime('%Y-%m-%d, %H:%M')

class CategoryTypeAdmin(SoftDeleteAdmin):

    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseCategory, CategoryTypeAdmin)
admin.site.register(ExpenseType, CategoryTypeAdmin)