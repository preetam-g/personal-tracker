from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('transaction/add/', views.add_transaction_view, name='add'),
    path('transaction/<int:tran_id>/edit/', views.edit_transaction_view, name='edit'),
    path('transaction/<int:tran_id>/delete/', views.delete_transaction_view, name='delete'),
    path('summary/', views.summary_view, name='summary'),
]