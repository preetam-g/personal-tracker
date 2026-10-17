from decimal import Decimal
from datetime import datetime, time
from functools import lru_cache

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import BillShare, GroupMembership, GroupPayment, SharedBill, SharedGroup


CENT = Decimal('0.01')
MAX_EXACT_BALANCES = 12


@transaction.atomic
def create_group(name, creator):
    group = SharedGroup.objects.create(name=name.strip(), created_by=creator)
    GroupMembership.objects.create(group=group, user=creator)
    return group


def add_member(group, user):
    membership, _ = GroupMembership.objects.get_or_create(group=group, user=user)
    return membership


def allocate_shares(amount, percentages):
    """Allocate every cent, giving rounding remainders to the largest fractions."""
    if not percentages or sum(percentages.values(), Decimal('0')) != Decimal('100'):
        raise ValidationError('The percentages must add up to 100%.')
    cents = int(amount * 100)
    raw = {user_id: Decimal(cents) * percent / 100 for user_id, percent in percentages.items()}
    allocated = {user_id: int(value) for user_id, value in raw.items()}
    leftover = cents - sum(allocated.values())
    order = sorted(raw, key=lambda user_id: (-(raw[user_id] - allocated[user_id]), user_id))
    for user_id in order[:leftover]:
        allocated[user_id] += 1
    return {user_id: Decimal(value) / 100 for user_id, value in allocated.items()}


def percentages_from_amounts(amounts):
    """Store display percentages in hundredths while preserving exact share amounts."""
    total = sum(amounts.values(), Decimal('0.00'))
    if not amounts or total <= 0 or len(amounts) > 10000:
        raise ValidationError('Enter valid amounts for the people in this bill.')
    available = 10000 - len(amounts)
    raw = {user_id: Decimal(available) * share / total for user_id, share in amounts.items()}
    units = {user_id: int(value) + 1 for user_id, value in raw.items()}
    leftover = 10000 - sum(units.values())
    order = sorted(raw, key=lambda user_id: (-(raw[user_id] - int(raw[user_id])), user_id))
    for user_id in order[:leftover]:
        units[user_id] += 1
    return {user_id: Decimal(value) / 100 for user_id, value in units.items()}


def sync_personal_expenses_for_bill(bill, previous_user_ids=()):
    from apps.expenses import cache as expense_cache
    from apps.expenses.models import Expense, ExpenseType
    from apps.forex.models import Currency

    inr = Currency.objects.get(code='INR')
    upi_type = ExpenseType.objects.get(name='UPI', user__isnull=True)
    date = timezone.make_aware(datetime.combine(bill.date, time(12, 0)))
    user_ids = set(previous_user_ids)
    for share in bill.shares.all():
        if share.amount <= 0:
            continue
        expense, created = Expense.objects.get_or_create(
            group_bill_share=share,
            defaults={
                'user_id': share.user_id,
                'date': date,
                'amount': share.amount,
                'amount_entered': share.amount,
                'currency': inr,
                'exchange_rate': Decimal('1'),
                'category': bill.category,
                'type': upi_type,
                'note': f'Group: {bill.group.name} / {bill.title}'[:50],
            },
        )
        if not created:
            expense.user_id = share.user_id
            expense.date = date
            expense.amount = share.amount
            expense.amount_entered = share.amount
            expense.currency = inr
            expense.exchange_rate = Decimal('1')
            expense.category = bill.category
            expense.type = upi_type
            expense.note = f'Group: {bill.group.name} / {bill.title}'[:50]
            expense.save(update_fields=[
                'user', 'date', 'amount', 'amount_entered', 'currency',
                'exchange_rate', 'category', 'type', 'note', 'updated_at',
            ])
        user_ids.add(share.user_id)
    def invalidate_expense_caches():
        for user_id in user_ids:
            expense_cache.invalidate_cache(user_id)

    transaction.on_commit(invalidate_expense_caches)


def bill_shares(group, amount, paid_by, percentages=None, amounts=None):
    member_ids = set(group.members.values_list('id', flat=True))
    if paid_by.id not in member_ids:
        raise ValidationError('The payer must belong to the group.')
    if amount <= 0 or amount != amount.quantize(CENT):
        raise ValidationError('Enter a positive amount in rupees and paise.')
    if (percentages is None) == (amounts is None):
        raise ValidationError('Choose one way to split the bill.')
    if amounts is not None:
        if not amounts or not set(amounts).issubset(member_ids):
            raise ValidationError('Every participant must belong to the group.')
        if any(share <= 0 or share != share.quantize(CENT) for share in amounts.values()):
            raise ValidationError('Each included participant needs a positive amount in rupees and paise.')
        if sum(amounts.values(), Decimal('0.00')) != amount:
            raise ValidationError('The share amounts must add up to the bill total.')
        shares = amounts
        percentages = percentages_from_amounts(amounts)
    else:
        if not percentages or not set(percentages).issubset(member_ids):
            raise ValidationError('Every participant must belong to the group.')
        if any(percent <= 0 or percent > 100 for percent in percentages.values()):
            raise ValidationError('Each included participant needs a percentage above 0%.')
        shares = allocate_shares(amount, percentages)
    return shares, percentages


@transaction.atomic
def create_bill(group, title, amount, date, paid_by, created_by, percentages=None, amounts=None, category=None):
    if not group.members.filter(pk=created_by.pk).exists():
        raise ValidationError('The creator must belong to the group.')
    shares, percentages = bill_shares(group, amount, paid_by, percentages, amounts)
    bill = SharedBill.objects.create(
        group=group, title=title.strip(), amount=amount, date=date,
        paid_by=paid_by, created_by=created_by, category=category,
    )
    BillShare.objects.bulk_create([
        BillShare(bill=bill, user_id=user_id, percentage=percentages[user_id], amount=share)
        for user_id, share in shares.items()
    ])
    sync_personal_expenses_for_bill(bill)
    return bill


@transaction.atomic
def update_bill(bill, editor, title, amount, date, percentages=None, amounts=None, category=None):
    SharedGroup.objects.select_for_update().get(pk=bill.group_id)
    bill = SharedBill.objects.select_for_update().get(pk=bill.pk)
    if bill.paid_by_id != editor.pk:
        raise ValidationError('Only the person who paid can edit this bill.')
    shares, percentages = bill_shares(bill.group, amount, bill.paid_by, percentages, amounts)
    existing = {share.user_id: share for share in bill.shares.select_for_update()}
    bill.title = title.strip()
    bill.amount = amount
    bill.date = date
    bill.category = category
    bill.save(update_fields=['title', 'amount', 'date', 'category', 'updated_at'])
    for user_id, share in existing.items():
        if user_id not in shares:
            share.delete()
        else:
            share.amount = shares[user_id]
            share.percentage = percentages[user_id]
            share.save(update_fields=['amount', 'percentage'])
    BillShare.objects.bulk_create([
        BillShare(bill=bill, user_id=user_id, amount=share, percentage=percentages[user_id])
        for user_id, share in shares.items() if user_id not in existing
    ])
    sync_personal_expenses_for_bill(bill, previous_user_ids=existing)
    return bill


@transaction.atomic
def record_payment(group, from_user, to_user, amount, date, created_by):
    member_ids = set(group.members.values_list('id', flat=True))
    if not {from_user.id, to_user.id, created_by.id}.issubset(member_ids):
        raise ValidationError('Everyone in a payment must belong to the group.')
    if from_user == to_user or amount <= 0 or amount != amount.quantize(CENT):
        raise ValidationError('Choose two different people and a positive amount.')
    return GroupPayment.objects.create(
        group=group, from_user=from_user, to_user=to_user,
        amount=amount, date=date, created_by=created_by,
    )


@transaction.atomic
def claim_payment(group, from_user, to_user, amount, reference):
    """A payer reports a UPI transfer; it remains untrusted until the receiver confirms it."""
    SharedGroup.objects.select_for_update().get(pk=group.pk)
    member_ids = set(group.members.values_list('id', flat=True))
    if not {from_user.pk, to_user.pk}.issubset(member_ids) or from_user == to_user:
        raise ValidationError('Choose two different members of this group.')
    if not to_user.upi_id:
        raise ValidationError('The receiver needs to add a UPI ID to their profile first.')
    if amount <= 0 or amount != amount.quantize(CENT):
        raise ValidationError('Enter a positive amount in rupees and paise.')
    balances = group_balances(group)
    pending_sent = GroupPayment.objects.filter(
        group=group, from_user=from_user, status=GroupPayment.Status.PENDING,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pending_received = GroupPayment.objects.filter(
        group=group, to_user=to_user, status=GroupPayment.Status.PENDING,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    available = min(-balances[from_user.pk] - pending_sent, balances[to_user.pk] - pending_received)
    if available < amount:
        raise ValidationError('This amount exceeds the current unsettled balance. Refresh the group.')
    return GroupPayment.objects.create(
        group=group, from_user=from_user, to_user=to_user, created_by=from_user,
        amount=amount, date=timezone.localdate(), status=GroupPayment.Status.PENDING,
        payee_upi_id=to_user.upi_id, payment_reference=reference[:64],
    )


@transaction.atomic
def confirm_payment(payment, receiver):
    SharedGroup.objects.select_for_update().get(pk=payment.group_id)
    payment = GroupPayment.objects.select_for_update().get(pk=payment.pk)
    if payment.to_user_id != receiver.pk or payment.status != GroupPayment.Status.PENDING:
        raise ValidationError('Only the receiver can confirm a pending payment.')
    balances = group_balances(payment.group)
    if payment.amount > min(-balances[payment.from_user_id], balances[payment.to_user_id]):
        raise ValidationError('Balances changed. This payment cannot be confirmed as entered.')
    payment.status = GroupPayment.Status.CONFIRMED
    payment.confirmed_at = timezone.now()
    payment.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    return payment


@transaction.atomic
def reject_payment(payment, receiver):
    SharedGroup.objects.select_for_update().get(pk=payment.group_id)
    payment = GroupPayment.objects.select_for_update().get(pk=payment.pk)
    if payment.to_user_id != receiver.pk or payment.status != GroupPayment.Status.PENDING:
        raise ValidationError('Only the receiver can reject a pending payment.')
    payment.status = GroupPayment.Status.REJECTED
    payment.save(update_fields=['status', 'updated_at'])
    return payment


@transaction.atomic
def edit_payment_amount(payment, receiver, amount):
    SharedGroup.objects.select_for_update().get(pk=payment.group_id)
    payment = GroupPayment.objects.select_for_update().get(pk=payment.pk)
    if payment.to_user_id != receiver.pk:
        raise ValidationError('Only the receiver can edit this payment.')
    if payment.status == GroupPayment.Status.REJECTED:
        raise ValidationError('Rejected payments cannot be edited.')
    if amount <= 0 or amount != amount.quantize(CENT):
        raise ValidationError('Enter a positive amount in rupees and paise.')
    balances = group_balances(payment.group)
    if payment.status == GroupPayment.Status.CONFIRMED:
        # Reconstruct balances without this transfer before validating its replacement.
        balances[payment.from_user_id] -= payment.amount
        balances[payment.to_user_id] += payment.amount
    else:
        if amount > payment.amount:
            raise ValidationError('A pending payment can only be corrected downwards.')
        pending = payment.group.payments.filter(status=GroupPayment.Status.PENDING).exclude(pk=payment.pk)
        for other in pending:
            balances[other.from_user_id] += other.amount
            balances[other.to_user_id] -= other.amount
    if amount > min(-balances[payment.from_user_id], balances[payment.to_user_id]):
        raise ValidationError('This amount exceeds the unsettled balance.')
    payment.amount = amount
    payment.save(update_fields=['amount', 'updated_at'])
    return payment


@transaction.atomic
def delete_payment(payment, receiver):
    SharedGroup.objects.select_for_update().get(pk=payment.group_id)
    payment = GroupPayment.objects.select_for_update().get(pk=payment.pk)
    if payment.to_user_id != receiver.pk:
        raise ValidationError('Only the receiver can delete this payment.')
    payment.delete()


def group_balances(group):
    """Positive means the group owes this person; negative means they owe."""
    balances = {member.id: Decimal('0.00') for member in group.members.all()}
    for bill in group.bills.prefetch_related('shares'):
        balances[bill.paid_by_id] += bill.amount
        for share in bill.shares.all():
            balances[share.user_id] -= share.amount
    for payment in group.payments.filter(status=GroupPayment.Status.CONFIRMED):
        balances[payment.from_user_id] += payment.amount
        balances[payment.to_user_id] -= payment.amount
    return balances


def simplify_balances(balances):
    """Find minimum transfers for small groups and bounded suggestions for large ones."""
    people = tuple(sorted(user_id for user_id, amount in balances.items() if amount))
    initial = tuple(int(balances[user_id] * 100) for user_id in people)
    if sum(initial) != 0:
        raise ValidationError('Group balances do not add up to zero.')

    if len(people) > MAX_EXACT_BALANCES:
        debtors = [[person, -amount] for person, amount in zip(people, initial) if amount < 0]
        creditors = [[person, amount] for person, amount in zip(people, initial) if amount > 0]
        debtors.sort(key=lambda item: -item[1])
        creditors.sort(key=lambda item: -item[1])
        result = []
        debtor_index = creditor_index = 0
        while debtor_index < len(debtors) and creditor_index < len(creditors):
            amount = min(debtors[debtor_index][1], creditors[creditor_index][1])
            result.append({
                'from_user_id': debtors[debtor_index][0],
                'to_user_id': creditors[creditor_index][0],
                'amount': Decimal(amount) / 100,
            })
            debtors[debtor_index][1] -= amount
            creditors[creditor_index][1] -= amount
            if not debtors[debtor_index][1]:
                debtor_index += 1
            if not creditors[creditor_index][1]:
                creditor_index += 1
        return result

    @lru_cache(maxsize=None)
    def solve(state):
        try:
            first = next(i for i, amount in enumerate(state) if amount)
        except StopIteration:
            return ()
        best = None
        seen = set()
        for other in range(first + 1, len(state)):
            if state[first] * state[other] >= 0 or state[other] in seen:
                continue
            seen.add(state[other])
            amount = min(abs(state[first]), abs(state[other]))
            remaining = list(state)
            if state[first] < 0:
                remaining[first] += amount
                remaining[other] -= amount
                transfer = (people[first], people[other], amount)
            else:
                remaining[first] -= amount
                remaining[other] += amount
                transfer = (people[other], people[first], amount)
            candidate = (transfer,) + solve(tuple(remaining))
            if best is None or len(candidate) < len(best):
                best = candidate
            if state[first] + state[other] == 0:
                break
        return best or ()

    return [
        {'from_user_id': sender, 'to_user_id': receiver, 'amount': Decimal(cents) / 100}
        for sender, receiver, cents in solve(initial)
    ]
