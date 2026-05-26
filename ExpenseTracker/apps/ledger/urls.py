from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('add/', views.add_transaction_view, name='add'),
    path('edit/<int:tran_id>/', views.edit_transaction_view, name='edit'),
    path('delete/<int:tran_id>/', views.delete_transaction_view, name='delete'),
    path('summary/', views.summary_view, name='summary'),
]