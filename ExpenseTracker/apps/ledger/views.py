from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.cache import cache as django_cache
from django.utils.timezone import localdate

from .forms import TransactionForm, LedgerHomeForm
from .models import Transaction, Contact
from .services import create_settlement
from . import cache

from apps.base.views import delete_object_view
from apps.base.utils import TimeFrame
from apps.base.navigation import redirect_to_next


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

    cache_key = cache.home_key(request.user.id, timeframe)
    transactions = django_cache.get_or_set(
        key=cache_key,
        default=lambda: list(
            Transaction.objects
            .for_user(request.user)
            .with_contact()
            .filter_with_form(filters)
        ),
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
            cache.invalidate_cache(request.user.id)
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
    if not transaction.can_be_edited:
        messages.error(
            request,
            message="Settled and Carry-forward transactions can not be edited."
        )
        return redirect_to_next(request, reverse('ledger:home'))

    if request.method == "POST":

        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            transaction= form.save()
            cache.invalidate_cache(request.user.id)
            messages.success(request, f'{transaction} has been updated.')
            return redirect_to_next(request, reverse("ledger:home"))

    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(request, "ledger/ledger_form.html", {"form": form})


@login_required(login_url='accounts:login')
def delete_transaction_view(request, tran_id):

    transaction = get_object_or_404(
        Transaction.objects.for_user(request.user),
        pk=tran_id,
    )
    if not transaction.can_be_deleted:
        messages.error(
            request,
            message="Settled and Carry-forward transactions can not be deleted."
        )
        return redirect_to_next(request, reverse('ledger:home'))

    return delete_object_view(
        request=request,
        model=Transaction,
        obj_id=tran_id,
        final_redirect_fallback="ledger:home",
        cache_delete_func=cache.invalidate_cache,
    )


@login_required(login_url='accounts:login')
def summary_view(request):

    cache_key = cache.summary_key(request.user.id)
    context_data = django_cache.get_or_set(
        key=cache_key,
        default = lambda: dict(
            Transaction.objects
            .for_user(request.user)
            .with_contact()
            .get_contacts_summary()
        )
    )
    return render(
        request,
        template_name='ledger/summary_page.html',
        context={
            **context_data,
        },
    )


@login_required(login_url='accounts:login')
def create_settlement_view(request, contact_id):

    contact = get_object_or_404(
        Contact.objects.for_user(request.user),
        pk=contact_id,
    )
    if request.method != "POST":
        return redirect_to_next(
            request,
            reverse('ledger:summary'),
        )

    try:
        create_settlement(contact)
    except ValidationError as e:
        messages.error(request, e.message)
    else:
        cache.invalidate_cache(request.user.id)
        messages.success(
            request,
            message=f'"{contact}" has been settled.',
        )

    return redirect_to_next(
        request,
        reverse('ledger:summary'),
    )