from django.contrib import admin
from .models import UserProfile
from apps.base.admin import SoftDeleteAdmin


class UserProfileAdmin(SoftDeleteAdmin):

    list_display = ['username', 'first_name', 'last_name', 'email', 'is_deleted']
    list_filter = ['username']


admin.site.register(UserProfile, UserProfileAdmin)