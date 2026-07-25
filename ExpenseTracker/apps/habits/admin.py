from django.contrib import admin

from .models import Habit, HabitPlan, DailyProgress

# Register your models here.
admin.site.register(Habit)
admin.site.register(HabitPlan)
admin.site.register(DailyProgress)