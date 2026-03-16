from django.urls import path
from . import views

app_name = "accounts" # namespace ( for linking we will use "accounts:signup" )
urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
]