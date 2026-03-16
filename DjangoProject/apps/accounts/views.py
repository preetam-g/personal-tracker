from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from . import forms


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


def update_profile_view(request):

    if request.method == 'POST':
        form = forms.UpdateUserForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, f"Your account has been updated successfully!")
            return redirect("home")
        else:
            messages.error(request, f"Something went wrong. Please try again.")

    else:
        form = forms.UpdateUserForm(instance=request.user)

        return render(request, "accounts/update_profile.html", {"form": form})
