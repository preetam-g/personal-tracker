from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts" # namespace ( for linking we will use "accounts:signup" )
urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    # path("password-change/", views.password_change_view, name="password_change"),
    #
    # path("password-reset/",
    #      auth_views.PasswordResetView.as_view(
    #          template_name="accounts/password_reset/password_reset.html",
    #          email_template_name="accounts/password_reset/password_reset_email.html",
    #          success_url=reverse_lazy("accounts:password_reset_done")
    #      ), name="password_reset"),
    # path("password-reset/done/",
    #      auth_views.PasswordResetDoneView.as_view(
    #         template_name="accounts/password_reset/password_reset_done.html",
    #      ), name="password_reset_done"),
    # path("password-reset/confirm/<uidb64>/<token>/",
    #      auth_views.PasswordResetConfirmView.as_view(
    #          template_name="accounts/password_reset/password_reset_confirm.html",
    #          success_url=reverse_lazy("accounts:password_reset_complete"),
    #      ), name="password_reset_confirm"),
    # path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
    #     template_name="accounts/password_reset/password_reset_complete.html",
    # ), name="password_reset_complete"),

    path("expense-filter-defaults/", views.expense_filter_defaults_view, name="expenses_filter_defaults"),
    path("ledger-defaults", views.ledger_defaults_view, name="ledger_defaults"),
    path("forex-features-preferences", views.forex_features_preferences_view, name="forex_features_preferences"),
]