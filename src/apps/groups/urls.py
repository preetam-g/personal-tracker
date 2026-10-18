from django.urls import path

from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.groups_view, name='home'),
    path('new/', views.create_group_view, name='create'),
    path('<int:group_id>/', views.group_detail_view, name='detail'),
    path('<int:group_id>/members/new/', views.add_group_member_view, name='add_member'),
    path('<int:group_id>/bills/new/', views.add_group_bill_view, name='add_bill'),
    path('<int:group_id>/bills/<int:bill_id>/edit/', views.edit_group_bill_view, name='edit_bill'),
    path('<int:group_id>/bills/<int:bill_id>/delete/', views.delete_group_bill_view, name='delete_bill'),
    path('<int:group_id>/payments/new/', views.add_group_payment_view, name='add_payment'),
    path('<int:group_id>/payments/<int:payment_id>/edit/', views.edit_group_payment_view, name='edit_payment'),
    path('<int:group_id>/payments/<int:payment_id>/confirm/', views.confirm_group_payment_view, name='confirm_payment'),
    path('<int:group_id>/payments/<int:payment_id>/reject/', views.reject_group_payment_view, name='reject_payment'),
    path('<int:group_id>/payments/<int:payment_id>/delete/', views.delete_group_payment_view, name='delete_payment'),
]
