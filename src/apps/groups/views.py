from urllib.parse import urlencode
from uuid import uuid4
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import render, get_object_or_404, reverse, redirect
from .forms import SharedGroupForm, AddMemberForm, SharedBillForm, GroupPaymentForm, PaymentAmountEditForm
from .models import SharedGroup, SharedBill, GroupPayment
from .services import (
    MAX_EXACT_BALANCES, add_member, confirm_payment, create_group,
    delete_payment, edit_payment_amount, group_balances, reject_payment, simplify_balances,
)
from apps.expenses import cache as expenses_cache


def _shared_group_for_user(user, group_id):
    return get_object_or_404(SharedGroup.objects.filter(members=user).distinct(), pk=group_id)


@login_required(login_url='accounts:login')
def groups_view(request):
    groups = SharedGroup.objects.filter(members=request.user).distinct().order_by('name')
    return render(request, 'groups/groups.html', {'groups': groups})


@login_required(login_url='accounts:login')
def create_group_view(request):
    form = SharedGroupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group = create_group(form.cleaned_data['name'], request.user)
        return redirect('groups:detail', group_id=group.pk)
    return render(request, 'groups/shared_form.html', {
        'form': form, 'title': 'Create a group', 'cancel_url': reverse('groups:home'),
    })


@login_required(login_url='accounts:login')
def group_detail_view(request, group_id):
    group = _shared_group_for_user(request.user, group_id)
    members = list(group.members.order_by('username'))
    users = {member.pk: member for member in members}
    balances = group_balances(group)
    pending_payments = list(group.payments.filter(
        status=GroupPayment.Status.PENDING,
    ).select_related('from_user', 'to_user'))
    available_balances = balances.copy()
    for payment in pending_payments:
        available_balances[payment.from_user_id] += payment.amount
        available_balances[payment.to_user_id] -= payment.amount
    balance_rows = [
        {'user': member, 'amount': balances[member.pk], 'absolute_amount': abs(balances[member.pk])}
        for member in members
    ]
    suggestions = []
    for item in simplify_balances(available_balances):
        sender = users[item['from_user_id']]
        receiver = users[item['to_user_id']]
        suggestion = {
            'sender': sender, 'receiver': receiver, 'amount': item['amount'],
        }
        if sender.pk == request.user.pk and receiver.upi_id:
            reference = f'TRK{uuid4().hex[:20]}'
            parameters = urlencode({
                'pa': receiver.upi_id, 'pn': receiver.get_full_name() or receiver.username,
                'am': f"{item['amount']:.2f}", 'cu': 'INR', 'tr': reference,
                'tn': f'{group.name} settlement'[:80],
            })
            suggestion.update({
                'reference': reference,
                'gpay_url': f'gpay://upi/pay?{parameters}',
                'cred_url': f'upi://pay?{parameters}',
            })
        suggestions.append(suggestion)
    bills = group.bills.select_related('paid_by', 'created_by').prefetch_related('shares__user')[:30]
    payments = group.payments.select_related('from_user', 'to_user', 'created_by')[:30]
    activity = sorted(
        [{'kind': 'bill', 'bill': bill, 'created_at': bill.created_at} for bill in bills]
        + [{'kind': 'payment', 'payment': payment, 'created_at': payment.created_at} for payment in payments],
        key=lambda item: item['created_at'], reverse=True,
    )
    return render(request, 'groups/group_detail.html', {
        'group': group, 'members': members, 'balance_rows': balance_rows,
        'suggestions': suggestions, 'activity': activity,
        'pending_payments': pending_payments,
        'exact_simplification': sum(bool(amount) for amount in available_balances.values()) <= MAX_EXACT_BALANCES,
    })


@login_required(login_url='accounts:login')
def add_group_member_view(request, group_id):
    group = _shared_group_for_user(request.user, group_id)
    if group.created_by_id != request.user.pk:
        raise PermissionDenied('Only the group creator can add people.')
    form = AddMemberForm(request.POST or None, group=group)
    if request.method == 'POST' and form.is_valid():
        add_member(group, form.member)
        messages.success(request, f'{form.member.username} joined the group.')
        return redirect('groups:detail', group_id=group.pk)
    return render(request, 'groups/shared_form.html', {
        'form': form, 'title': f'Add someone to {group.name}',
        'hint': 'They need to sign up first. Enter their username exactly as shown on their profile.',
        'cancel_url': reverse('groups:detail', kwargs={'group_id': group.pk}),
    })


@login_required(login_url='accounts:login')
def add_group_bill_view(request, group_id):
    group = _shared_group_for_user(request.user, group_id)
    form = SharedBillForm(request.POST or None, group=group)
    if request.method == 'POST' and form.is_valid():
        form.save(created_by=request.user)
        messages.success(request, 'Bill added to the group.')
        return redirect('groups:detail', group_id=group.pk)
    return render(request, 'groups/shared_bill_form.html', {
        'form': form, 'group': group, 'editing': False,
        'cancel_url': reverse('groups:detail', kwargs={'group_id': group.pk}),
    })


@login_required(login_url='accounts:login')
def edit_group_bill_view(request, group_id, bill_id):
    group = _shared_group_for_user(request.user, group_id)
    bill = get_object_or_404(SharedBill, pk=bill_id, group=group)
    if bill.paid_by_id != request.user.pk:
        raise PermissionDenied('Only the person who paid can edit this bill.')
    form = SharedBillForm(request.POST or None, group=group, instance=bill)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save(created_by=request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Bill updated.')
            return redirect('groups:detail', group_id=group.pk)
    return render(request, 'groups/shared_bill_form.html', {
        'form': form, 'group': group, 'editing': True,
        'cancel_url': reverse('groups:detail', kwargs={'group_id': group.pk}),
    })


@login_required(login_url='accounts:login')
def add_group_payment_view(request, group_id):
    group = _shared_group_for_user(request.user, group_id)
    if request.method != 'POST':
        return redirect('groups:detail', group_id=group.pk)
    form = GroupPaymentForm(request.POST, group=group, sender=request.user)
    if form.is_valid():
        try:
            form.save()
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Payment submitted. The receiver must confirm it before balances change.')
    else:
        messages.error(request, 'Check the payment details and try again.')
    return redirect('groups:detail', group_id=group.pk)


@login_required(login_url='accounts:login')
def confirm_group_payment_view(request, group_id, payment_id):
    group = _shared_group_for_user(request.user, group_id)
    payment = get_object_or_404(GroupPayment, pk=payment_id, group=group)
    if request.method != 'POST':
        raise PermissionDenied('Use the confirm button.')
    try:
        confirm_payment(payment, request.user)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    else:
        messages.success(request, 'Payment confirmed. Group balances are updated.')
    return redirect('groups:detail', group_id=group.pk)


@login_required(login_url='accounts:login')
def reject_group_payment_view(request, group_id, payment_id):
    group = _shared_group_for_user(request.user, group_id)
    payment = get_object_or_404(GroupPayment, pk=payment_id, group=group)
    if request.method != 'POST':
        raise PermissionDenied('Use the reject button.')
    try:
        reject_payment(payment, request.user)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    else:
        messages.success(request, 'Payment request rejected. Balances have not changed.')
    return redirect('groups:detail', group_id=group.pk)


@login_required(login_url='accounts:login')
def delete_group_bill_view(request, group_id, bill_id):
    group = _shared_group_for_user(request.user, group_id)
    bill = get_object_or_404(SharedBill, pk=bill_id, group=group)
    if request.method != 'POST':
        raise PermissionDenied('Use the delete button to remove a bill.')
    if request.user.pk != bill.paid_by_id:
        raise PermissionDenied('Only the person who paid can remove this bill.')
    user_ids = list(bill.shares.values_list('user_id', flat=True))
    with transaction.atomic():
        bill.delete()
        def invalidate_expense_caches():
            for user_id in user_ids:
                expenses_cache.invalidate_cache(user_id)
        transaction.on_commit(invalidate_expense_caches)
    messages.success(request, 'Bill removed.')
    return redirect('groups:detail', group_id=group.pk)


@login_required(login_url='accounts:login')
def edit_group_payment_view(request, group_id, payment_id):
    group = _shared_group_for_user(request.user, group_id)
    payment = get_object_or_404(GroupPayment, pk=payment_id, group=group)
    if request.method != 'POST':
        raise PermissionDenied('Use the edit form.')
    if request.user.pk != payment.to_user_id:
        raise PermissionDenied('Only the receiver can edit this payment.')
    form = PaymentAmountEditForm(request.POST)
    if form.is_valid():
        try:
            edit_payment_amount(payment, request.user, form.cleaned_data['amount'])
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Payment amount updated.')
    else:
        messages.error(request, 'Enter a valid payment amount.')
    return redirect('groups:detail', group_id=group.pk)


@login_required(login_url='accounts:login')
def delete_group_payment_view(request, group_id, payment_id):
    group = _shared_group_for_user(request.user, group_id)
    payment = get_object_or_404(GroupPayment, pk=payment_id, group=group)
    if request.method != 'POST':
        raise PermissionDenied('Use the delete button to remove a payment.')
    if request.user.pk != payment.to_user_id:
        raise PermissionDenied('Only the receiver can delete this payment.')
    delete_payment(payment, request.user)
    messages.success(request, 'Payment removed.')
    return redirect('groups:detail', group_id=group.pk)
