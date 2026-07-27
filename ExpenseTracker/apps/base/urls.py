from django.urls import path
from . import views

app_name = 'base'
urlpatterns = [
    path('preferences/', views.preferences_view, name='preferences'),
    path('category/add/', views.add_category_view, name='add_category'),
    path('category/<int:cat_id>/edit/', views.edit_category_view, name='edit_category'),
    path('category/<int:cat_id>/delete/', views.delete_category_view, name='delete_category'),
    path('type/add/', views.add_type_view, name='add_type'),
    path('type/<int:type_id>/edit/', views.edit_type_view, name='edit_type'),
    path('type/<int:type_id>/delete/', views.delete_type_view, name='delete_type'),
    path('contact/add/', views.add_contact_view, name='add_contact'),
    path('contact/<int:cont_id>/edit/', views.edit_contact_view, name='edit_contact'),
    path('contact/<int:cont_id>/delete/', views.delete_contact_view, name='delete_contact'),
]