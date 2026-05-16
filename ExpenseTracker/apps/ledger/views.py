from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import TransactionForm
from .models import Transaction


@login_required(login_url='login')
def home_view(request):
    qs = Transaction.objects.all_for_user(request.user)[:10]
    return render(request, 'ledger/home.html', {"transactions": qs})


@login_required(login_url='login')
def add_transaction(request):

    if request.method == "POST":

        form = TransactionForm(request.POST, user=request.user)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            messages.success(request, 'Transaction has been added.')
            return redirect("ledger:home")

    else:
        form = TransactionForm(user=request.user)

    return render(request, "ledger/ledger_form.html", {"form": form})