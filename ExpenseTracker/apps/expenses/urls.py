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
    path('preferences/', views.preferences_view, name='preferences'),
    path('category/add/', views.add_category_view, name='add_category'),
    path('category/edit/<int:cat_id>/', views.edit_category_view, name='edit_category'),
    path('category/delete/<int:cat_id>/', views.delete_category_view, name='delete_category'),
    path('type/add/', views.add_type_view, name='add_type'),
    path('type/edit/<int:type_id>/', views.edit_type_view, name='edit_type'),
    path('type/delete/<int:type_id>/', views.delete_type_view, name='delete_type'),
]