from django.contrib import admin

class SoftDeleteAdmin(admin.ModelAdmin):

    base_list_display = ['is_deleted']
    base_list_filter = ['is_deleted']

    def get_queryset(self, request):
        return self.model.all_objects.all()

    def get_list_display(self, request):
        current = list(super().get_list_display(request))
        return list(dict.fromkeys(current + self.base_list_display))

    def get_list_filter(self, request):
        current = list(super().get_list_filter(request))
        return list(dict.fromkeys(current + self.base_list_filter))