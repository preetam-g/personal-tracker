from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('add_habit/', views.add_habit_view, name='add_habit'),
    path('edit_habit/<int:habit_id>', views.edit_habit_view, name='edit_habit'),
    path('delete_habit/<int:habit_id>', views.delete_habit_view, name='delete_habit'),
    path('manage_habits/', views.manage_habits_view, name='manage_habits'),
]