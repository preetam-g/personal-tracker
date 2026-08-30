from decimal import Decimal
from datetime import datetime, time

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Transaction, TransactionSettlement
from .utils import TransactionType


def create_settlement(contact):

    with transaction.atomic():

        transactions = list(
            Transaction.objects
            .filter(
                contact=contact,
                is_settled=False,
                carry_forward_settlement__isnull=True,
            )
        )
        if not transactions:
            raise ValidationError(
                "There are no unsettled transactions to settle."
            )

        balance = -sum(
            (t.signed_amount for t in transactions),
            Decimal('0.00'),
        )

        settlement = TransactionSettlement.objects.create(
            contact=contact,
        )

        carry_forward = None
        carry_forward_date = timezone.make_aware(
            datetime.combine(
                timezone.localdate(),
                time.min,
            )
        )
        if balance != 0:
            if balance > 0:
                carry_forward_type = TransactionType.MONEY_SENT
            else:
                carry_forward_type = TransactionType.MONEY_RECEIVED

            carry_forward = Transaction.objects.create(
                contact=contact,
                amount=abs(balance),
                type=carry_forward_type,
                date=carry_forward_date,
                note=f"Carry-forward from settlement on {carry_forward_date.strftime('%d %b %Y')}.",
                is_settled=False,
            )

            settlement.carry_forward_transaction = carry_forward
            settlement.save()

        Transaction.objects.filter(
            pk__in=[t.pk for t in transactions]
        ).update(
            is_settled=True,
            settlement=settlement,
        )

        return settlement