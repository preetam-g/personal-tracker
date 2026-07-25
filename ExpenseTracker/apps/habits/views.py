from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url="accounts:login")
def home_view(request):
    return render(request, 'habits/home.html')