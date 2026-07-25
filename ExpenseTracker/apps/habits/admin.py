from django.contrib import admin

from .models import Habit, HabitGoal, DailyProgress

# Register your models here.
admin.site.register(Habit)
admin.site.register(HabitGoal)
admin.site.register(DailyProgress)
