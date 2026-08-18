from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    path('home/', views.home_view, name='home'),

    path('history/', views.history_view, name='history'),

    path('manage/', views.manage_habits_view, name='manage_habits'),

    path('habit/add/', views.add_habit_view, name='add_habit'),
    path('habit/<int:habit_id>/edit/', views.edit_habit_view, name='edit_habit'),
    path('habit/<int:habit_id>/delete/', views.delete_habit_view, name='delete_habit'),
    path('habit/<int:habit_id>/archive/', views.archive_habit_view, name='archive_habit'),
    path('habit/<int:habit_id>/unarchive/', views.unarchive_habit_view, name='unarchive_habit'),

    path('goal/add/', views.add_habit_plan_view, name='add_goal'),
    path('goal/<int:plan_id>/edit/', views.edit_habit_plan_view, name='edit_goal'),
    path('goal/<int:plan_id>/end/', views.end_habit_plan_view, name='end_goal'),
    path('goal/<int:plan_id>/delete/', views.delete_habit_plan_view, name='delete_goal'),
    path('goal/<int:plan_id>/detail/', views.detail_habit_plan_view, name='detail_goal'),
    path('goal/<int:plan_id>/restart/', views.restart_habit_plan_view, name='restart_goal'),

    path('progress/<int:prog_id>/edit/', views.edit_daily_progress_view, name='edit_daily_progress'),
    path('progress/<int:prog_id>/mark_completed/', views.mark_completed_daily_progress_view, name='mark_progress_completed'),

]