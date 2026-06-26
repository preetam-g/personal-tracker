from django.db import models
from django.core.cache import cache

from apps.ledger.cache_keys import LEDGER_PREFIX


class TransactionType(models.TextChoices):

    # BORROWED = 'BORROWED', 'Borrowed'
    # LENT = 'LENT', 'Lent'
    MONEY_SENT = 'MONEY_SENT', 'Money Sent'
    MONEY_RECEIVED = 'MONEY_RECEIVED', 'Money Received'

    @classmethod
    def outgoing_types(cls):
        return (
            cls.MONEY_SENT,
            # cls.LENT
        )

    @classmethod
    def incoming_types(cls):
        return (
            cls.MONEY_RECEIVED,
            # cls.BORROWED,
        )

class LinkStatus(models.TextChoices):
    UNLINKED = 'unlinked', 'Unlinked'
    PENDING = 'pending', 'Pending'
    LINKED = 'confirmed', 'Confirmed'


def invalidate_ledger_caches(ledger) -> bool:
    return cache.delete_pattern(
        f"{LEDGER_PREFIX}:user:{ledger.user_id}:*",
    )