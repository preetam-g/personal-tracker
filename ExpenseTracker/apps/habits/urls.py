from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('manage/', views.manage_habits_view, name='manage_habits'),
    path('habit/add/', views.add_habit_view, name='add_habit'),
    path('habit/<int:habit_id>/edit/', views.edit_habit_view, name='edit_habit'),
    path('habit/<int:habit_id>/delete/', views.delete_habit_view, name='delete_habit'),
    path('goal/add/', views.add_habit_plan_view, name='add_goal'),
    path('goal/<int:plan_id>/edit/', views.edit_habit_plan_view, name='edit_goal'),
    path('goal/<int:plan_id>/delete/', views.delete_habit_plan_view, name='delete_goal'),
    path('progress/<int:prog_id>/edit/', views.edit_daily_progress_view, name='edit_daily_progress'),
]