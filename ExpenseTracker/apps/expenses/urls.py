from django.urls import path
from . import views

app_name = 'expenses'
urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('home/', views.home_view, name='home'),
    path('add/', views.add_expense_view, name='add'),
    path('edit/<int:exp_id>/', views.edit_expense_view, name='edit'),
    path('delete/<int:exp_id>/', views.delete_expense_view, name='delete'),
    path('activity/', views.filtered_expense_view, name='summary'),
]