from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('add/', views.add_transaction, name='add'),
]