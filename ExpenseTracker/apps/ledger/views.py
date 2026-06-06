from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .forms import TransactionForm, LedgerFilterForm
from .models import Transaction

from apps.base.views import delete_object_view


@login_required(login_url='login')
def home_view(request):

    form = LedgerFilterForm(
        request.GET or None,
        user=request.user,
        preference_key='ledger_home_defaults',
    )
    filters = form.cleaned_data if form.is_valid() else form.initial
    transactions = Transaction.objects.filtered_for_user(
        user=request.user,
        filter_form=filters,
    )

    return render(
        request,
        'ledger/home.html',
        {
            "transactions": transactions,
            "form": form,
        },
    )


@login_required(login_url='login')
def add_transaction_view(request):

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


@login_required(login_url='login')
def edit_transaction_view(request, tran_id):

    transaction = get_object_or_404(Transaction, id=tran_id, user=request.user)

    if request.method == "POST":

        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction has been updated.')
        else:
            messages.error(request, 'Failed to update. Please try again later.')

        return redirect("ledger:home")

    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(request, "ledger/ledger_form.html", {"form": form})


@login_required(login_url='login')
def delete_transaction_view(request, tran_id):
    return delete_object_view(
        request=request,
        model=Transaction,
        name="Transaction",
        obj_id=tran_id,
        final_redirect="ledger:home"
    )


@login_required(login_url='login')
def summary_view(request):

    form = LedgerFilterForm(
        request.GET or None,
        user=request.user,
        preference_key="ledger_summary_defaults",
    )
    if form.is_valid():
        filters = form.cleaned_data
    else:
        filters = form.initial

    context_data = Transaction.objects.get_contacts_summary(request.user, filters)
    return render(
        request,
        template_name='ledger/summary_page.html',
        context={
            'form': form,
            **context_data,
        },
    )