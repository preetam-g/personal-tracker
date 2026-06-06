from django.db import models
from django.core.cache import cache

from apps.ledger.cache_keys import LEDGER_PREFIX


class TransactionType(models.TextChoices):

    BORROWED = 'BORROWED', 'Borrowed'
    LENT = 'LENT', 'Lent'
    PAYMENT_SENT = 'PAYMENT_SENT', 'Payment Sent'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'

    @classmethod
    def outgoing_types(cls):
        return (
            cls.PAYMENT_SENT,
            cls.LENT
        )

    @classmethod
    def incoming_types(cls):
        return (
            cls.PAYMENT_RECEIVED,
            cls.BORROWED,
        )

class LinkStatus(models.TextChoices):
    UNLINKED = 'unlinked', 'Unlinked'
    PENDING = 'pending', 'Pending'
    LINKED = 'confirmed', 'Confirmed'


def invalidate_ledger_caches(ledger) -> bool:
    return cache.delete_pattern(
        f"{LEDGER_PREFIX}:user:{ledger.user_id}:*",
    )