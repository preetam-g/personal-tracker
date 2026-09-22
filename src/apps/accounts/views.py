from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required

from . import forms
from .utils import serialize_form_data

from apps.expenses import forms as expenses_forms
from apps.ledger import forms as ledger_forms
from apps.forex.forms import ForexFeaturesForm

Profile = get_user_model()


def signup_view(request):

    if request.method == 'POST': # POST ( when submit is clicked )

        form = forms.SignupForm(request.POST)

        if form.is_valid(): # form validation
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}.")
            return redirect("home")

    else:
        form = forms.SignupForm() # GET ( create empty form )

    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):

    if request.method == 'POST':

        form = forms.LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")

    else:
        form = forms.LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect("home")


@login_required(login_url='accounts:login')
def profile_view(request):

    if request.method == 'POST':

        form = forms.UpdateUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Profile updated successfully!")
            return redirect("accounts:profile")
        else:
            messages.error(request, f"Something went wrong!")

    else:
        form = forms.UpdateUserForm(instance=request.user)

    context = {
        'form': form,
        'profile': request.user,
    }

    return render(request, "accounts/profile.html", context)


@login_required(login_url='accounts:login')
def password_change_view(request):

    if request.method == 'POST':
        form = forms.PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, f"Your password was successfully updated!")
            return redirect("home")
        else:
            messages.error(request, f"Something went wrong. Please try again.")

    else:
        form = forms.PasswordChangeForm(request.user)

    return render(request,"accounts/password_change.html",{"form": form})


@login_required(login_url='accounts:login')
def expense_filter_defaults_view(request):

    if request.method != 'POST':
        return redirect('base:preferences')

    preferences = request.user.preferences
    form = expenses_forms.ExpenseFilterDefaultsForm(request.POST, user=request.user)
    if form.is_valid():

        preferences.set_expenses_preferences(
            expenses_filter_defaults=serialize_form_data(form.cleaned_data)
        )

        messages.success(
            request,
            'Expense filter defaults saved successfully.'
        )
    else:
        messages.error(request, "Something went wrong. Please try again.")

    return redirect("base:preferences")


@login_required(login_url='accounts:login')
def ledger_defaults_view(request):

    if request.method != 'POST':
        return redirect('base:preferences')

    preferences = request.user.preferences
    form = ledger_forms.LedgerDefaultsForm(request.POST, user=request.user)
    if form.is_valid():

        preferences.set_ledger_preferences(
            ledger_defaults=serialize_form_data(form.cleaned_data)
        )
        messages.success(
            request,
            'Ledger defaults saved successfully.'
        )
    else:
        messages.error(request, "Something went wrong. Please try again.")


    return redirect("base:preferences")


@login_required(login_url='accounts:login')
def forex_features_preferences_view(request):

    if request.method != 'POST':
        return redirect('base:preferences')

    preferences = request.user.preferences
    form = ForexFeaturesForm(
        request.POST,
        instance=preferences,
        user=request.user,
    )

    if form.is_valid():
        form.save()
        messages.success(
            request,
            'Forex preferences updated successfully.'
        )
    else:
        messages.error(
            request,
            'Unable to update forex preferences.'
        )

    return redirect('base:preferences')