from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .forms import TransactionForm, SummaryFilterForm
from .models import Transaction

from apps.base.views import delete_object_view
from apps.base.utils import get_start_date, TimeFrame


@login_required(login_url='login')
def home_view(request):
    qs = Transaction.objects.all_for_user(request.user)
    return render(request, 'ledger/home.html', {"transactions": qs})


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

    fallback_data = {
        'start_date': get_start_date(timezone.localdate(), TimeFrame.THIS_MONTH),
        'end_date': timezone.localdate(),
    }

    data = request.GET.copy()
    if not data:
        data = fallback_data

    form = SummaryFilterForm(data)
    if form.is_valid():
        context_data = Transaction.objects.get_contacts_summary(request.user, form.cleaned_data)
    else:
        form = SummaryFilterForm(fallback_data, user=request.user)
        context_data = Transaction.objects.get_contacts_summary(request.user, form.cleaned_data)

    return render(
        request,
        template_name='ledger/summary_page.html',
        context={
            'form': form,
            **context_data,
        },
    )