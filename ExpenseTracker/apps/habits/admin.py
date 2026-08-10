from django.contrib import admin

from .models import Habit, HabitPlan, DailyProgress

admin.site.register(Habit)
admin.site.register(HabitPlan)
admin.site.register(DailyProgress)