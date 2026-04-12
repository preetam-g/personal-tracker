from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from apps.base.admin import SoftDeleteAdmin
from apps.expenses.models import Expense, ExpenseCategory, ExpenseType


class CategoryTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: ExpenseCategory | ExpenseType):
        if obj.user:
            return f"{obj.name} [{obj.user.username}]"
        return f"{obj.name} [GLOBAL]"


class ExpenseAdminForm(forms.ModelForm):
    category = CategoryTypeChoiceField(
        queryset=ExpenseCategory.objects.all()
    )
    type = CategoryTypeChoiceField(
        queryset=ExpenseType.objects.all()
    )

    class Meta:
        model = Expense
        fields = '__all__'


class ExpenseAdmin(SoftDeleteAdmin):
    list_display = ('formatted_date', 'amount', 'category', 'type', 'user')
    list_filter = ('category', 'type')
    form = ExpenseAdminForm

    @admin.display(description='Date', ordering='-date')
    def formatted_date(self, obj):
        return timezone.localtime(obj.date).strftime('%Y-%m-%d, %H:%M')


class CategoryTypeAdmin(SoftDeleteAdmin):
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

    def get_merge_target(self, queryset):
        """
        Prefer global item as target.
        Otherwise, promote first item to global.
        """
        global_item = queryset.filter(user__isnull=True).first()
        if global_item:
            return global_item

        target = queryset.first()
        target.user = None
        target.save()
        return target

    def reassign_related_objects(self, model, source, target):
        """
        Dynamically update related Expense fields
        """
        field_map = {
            ExpenseCategory: 'category',
            ExpenseType: 'type',
        }

        field_name = field_map.get(model)

        if field_name:
            Expense.all_objects.filter(**{field_name: source}).update(
                **{field_name: target}
            )

    @admin.action(description='Merge selected items into another')
    def merge_items(self, request, queryset):

        if queryset.count() < 2:
            self.message_user(
                request,
                'Select at least 2 items to merge.',
                level=messages.ERROR
            )
            return

        target = self.get_merge_target(queryset)
        sources = queryset.exclude(pk=target.pk)

        with transaction.atomic():
            for source in sources:
                self.reassign_related_objects(type(source), source, target)
                source.delete()

        self.message_user(
            request,
            f'Merged {sources.count()} items into "{target.name}".',
            level=messages.SUCCESS
        )


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseCategory, CategoryTypeAdmin)
admin.site.register(ExpenseType, CategoryTypeAdmin)