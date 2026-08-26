from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, reverse
from django.contrib import messages
from django.utils.timezone import localdate

from .forms import TransactionForm, LedgerSummaryForm, LedgerHomeForm
from .models import Transaction

from apps.base.views import delete_object_view
from apps.base.utils import TimeFrame
from ..base.navigation import redirect_to_next


@login_required(login_url='accounts:login')
def home_view(request):

    form = LedgerHomeForm(
        request.GET or None,
        user=request.user,
    )

    form_data = form.cleaned_data if form.is_valid() else form.initial
    timeframe = form_data.get('timeframe')

    today = localdate()
    filters = {
        'start_date': TimeFrame.get_start_date(today, timeframe),
        'end_date': today,
    }

    transactions = (
        Transaction.objects
        .for_user(request.user)
        .with_contact()
        .filter_with_form(filters)
    )

    return render(
        request,
        'ledger/home.html',
        {
            "transactions": transactions,
            "form": form,
        },
    )


@login_required(login_url='accounts:login')
def add_transaction_view(request):

    if request.method == "POST":

        form = TransactionForm(request.POST, user=request.user)

        if form.is_valid():
            transaction = form.save()
            messages.success(request, f"{transaction} has been added.")
            return redirect_to_next(request, reverse('ledger:home'))

    else:
        form = TransactionForm(user=request.user)

    return render(
        request,
        template_name="ledger/ledger_form.html",
        context={
            "form": form,
            "form-id": 'add-transaction-form',
            "item_name": 'Transaction',
        }
    )


@login_required(login_url='accounts:login')
def edit_transaction_view(request, tran_id):

    transaction = get_object_or_404(
        Transaction.objects.for_user(request.user),
        pk=tran_id,
    )

    if request.method == "POST":

        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction has been updated.')
        else:
            messages.error(request, 'Failed to update. Please try again later.')

        return redirect_to_next(request, reverse("ledger:home"))

    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(request, "ledger/ledger_form.html", {"form": form})


@login_required(login_url='accounts:login')
def delete_transaction_view(request, tran_id):
    return delete_object_view(
        request=request,
        model=Transaction,
        obj_id=tran_id,
        final_redirect_fallback="ledger:home",
    )


@login_required(login_url='accounts:login')
def summary_view(request):

    form = LedgerSummaryForm(
        request.GET or None,
        user=request.user,
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