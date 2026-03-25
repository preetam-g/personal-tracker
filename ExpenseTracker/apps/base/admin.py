from django.contrib import admin

@admin.action(description="Restore Selected Item(s)")
def restore_soft_deleted(modeladmin, request, queryset):
    count = queryset.restore()
    modeladmin.message_user(request, f"{count} item(s) restored successfully")


class SoftDeleteAdmin(admin.ModelAdmin):

    actions = [restore_soft_deleted]
    base_list_display = ['is_deleted']
    base_list_filter = ['is_deleted']
    base_actions = [restore_soft_deleted]

    def get_queryset(self, request):
        return self.model.all_objects.all()

    def get_list_display(self, request):
        current = list(super().get_list_display(request))
        return list(dict.fromkeys(current + self.base_list_display))

    def get_list_filter(self, request):
        current = list(super().get_list_filter(request))
        return list(dict.fromkeys(current + self.base_list_filter))

    def get_actions(self, request):
        actions = super().get_actions(request)

        for action_func in self.base_actions:
            action_name = action_func.__name__
            if action_name not in actions:
                description = getattr(
                    action_func,
                    'short_description',
                    getattr(action_func, "description", action_name)
                )
                actions[action_name] = (action_func, action_name, description)

        return actions