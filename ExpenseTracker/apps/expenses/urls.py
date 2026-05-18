from django.urls import path
from . import views

app_name = 'expenses'
urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('activity/', views.filtered_expense_view, name='summary'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('expense/add/', views.add_expense_view, name='add'),
    path('expense/edit/<int:exp_id>/', views.edit_expense_view, name='edit'),
    path('expense/delete/<int:exp_id>/', views.delete_expense_view, name='delete'),
]