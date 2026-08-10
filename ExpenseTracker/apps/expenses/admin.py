from django import forms
from django.contrib import admin
from django.utils import timezone

from apps.expenses.models import Expense, ExpenseCategory, ExpenseType


class CategoryTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: ExpenseCategory | ExpenseType):
        if obj.user:
            return f"{obj.name} [{obj.user.username}]"
        return f"{obj.name} [GLOBAL]"


class ExpenseAdminForm(forms.ModelForm):
    category = CategoryTypeChoiceField(
        queryset=ExpenseCategory.objects.all(),
        required=False,
    )
    type = CategoryTypeChoiceField(
        queryset=ExpenseType.objects.all(),
        required=False,
    )

    class Meta:
        model = Expense
        fields = '__all__'


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('formatted_date', 'amount', 'category', 'type', 'user')
    list_filter = ('category', 'type')
    form = ExpenseAdminForm

    @admin.display(description='Date', ordering='-date')
    def formatted_date(self, obj):
        return timezone.localtime(obj.date).strftime('%Y-%m-%d, %H:%M')


class CategoryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_display', 'user_id_display')
    search_fields = ('name', 'user__username')
    autocomplete_fields = ('user',)
    actions = ['merge_items']

    @admin.display(description='Username')
    def user_display(self, obj):
        return obj.user.username if obj.user else "GLOBAL"

    @admin.display(description='User ID')
    def user_id_display(self, obj):
        return obj.user.id if obj.user else "-"


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseCategory, CategoryTypeAdmin)
admin.site.register(ExpenseType, CategoryTypeAdmin)