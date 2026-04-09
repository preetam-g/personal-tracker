from django.contrib import admin, messages
from django.db import transaction

from apps.base.admin import SoftDeleteAdmin
from apps.expenses.models import Expense, ExpenseCategory, ExpenseType
from django.utils import timezone


def get_merge_target(queryset):
    global_item = queryset.filter(user__isnull=True).first()
    if global_item:
        return global_item
    return queryset.first()


class ExpenseAdmin(SoftDeleteAdmin):

    list_display = ('formatted_date', 'amount', 'category', 'type', 'user')
    list_filter =  ('category', 'type')

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

    @admin.action(description='Merge selected items into another')
    def merge_items(self, request, queryset):

        if queryset.count() < 2:
            self.message_user(
                request,
                'You must select at least 2 items to merge',
                level=messages.ERROR
            )
            return

        global_target = queryset.filter(user__isnull=True).first()

        if global_target:
            target = global_target
        else:
            target = queryset.first()
            target.user = None
            target.save()

        sources = queryset.exclude(pk=target.pk)

        with transaction.atomic():

            for source in sources:
                if isinstance(source, ExpenseCategory):
                    Expense.all_objects.filter(category=source).update(category=target)

                elif isinstance(source, ExpenseType):
                    Expense.all_objects.filter(type=source).update(type=target)

                source.delete()

        self.message_user(
            request,
            f"Merged {sources.count()} items into {target.name}",
            level=messages.SUCCESS
        )


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseCategory, CategoryTypeAdmin)
admin.site.register(ExpenseType, CategoryTypeAdmin)