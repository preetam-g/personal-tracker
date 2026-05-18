from django.urls import path
from . import views

app_name = 'base'
urlpatterns = [
    path('preferences/', views.preferences_view, name='preferences'),
    path('category/add/', views.add_category_view, name='add_category'),
    path('category/edit/<int:cat_id>/', views.edit_category_view, name='edit_category'),
    path('category/delete/<int:cat_id>/', views.delete_category_view, name='delete_category'),
    path('type/add/', views.add_type_view, name='add_type'),
    path('type/edit/<int:type_id>/', views.edit_type_view, name='edit_type'),
    path('type/delete/<int:type_id>/', views.delete_type_view, name='delete_type'),
    path('contact/add/', views.add_contact_view, name='add_contact'),
    path('contact/edit/<int:cont_id>/', views.edit_contact_view, name='edit_contact'),
    path('contact/delete/<int:cont_id>/', views.delete_contact_view, name='delete_contact'),
]