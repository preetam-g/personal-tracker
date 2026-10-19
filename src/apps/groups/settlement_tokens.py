from decimal import Decimal, InvalidOperation

from django.core import signing
from django.core.exceptions import ValidationError


TOKEN_SALT = 'groups.upi.destination.v1'


def suggested_payee_name(receiver):
    # A historical display name, never evidence of bank ownership.
    return (receiver.upi_account_name or receiver.get_full_name() or receiver.username)[:99]


def validate_payment_amount(amount):
    try:
        value = Decimal(str(amount))
        if not value.is_finite() or value <= 0 or value > Decimal('9999999999.99') or value != value.quantize(Decimal('0.01')):
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Enter a positive amount with at most two decimal places.')
    return value


def payment_token(group, sender, receiver, amount, reference):
    return signing.dumps({
        'group': group.pk, 'sender': sender.pk, 'receiver': receiver.pk,
        'upi': receiver.upi_id, 'name': suggested_payee_name(receiver),
        'limit': str(validate_payment_amount(amount)), 'reference': reference,
    }, salt=TOKEN_SALT)


def read_payment_token(token, group, sender, receiver, amount, reference=None):
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=86400)
        if (data['group'], data['sender'], data['receiver']) != (group.pk, sender.pk, receiver.pk):
            raise ValueError
        if reference is not None and data['reference'] != reference:
            raise ValueError
        if validate_payment_amount(amount) > validate_payment_amount(data['limit']):
            raise ValueError
    except (signing.BadSignature, KeyError, TypeError, ValueError, ValidationError):
        raise ValidationError('Payment details expired or changed. Reopen Settle Up and verify the receiver.')
    return data
