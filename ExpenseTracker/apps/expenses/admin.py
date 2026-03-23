from django.contrib import admin
from apps.expenses.models import *

admin.site.register(Expense)
admin.site.register(ExpenseCategory)
admin.site.register(ExpenseType)