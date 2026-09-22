from django.db import models


class TransactionType(models.TextChoices):

    MONEY_SENT = 'MONEY_SENT', 'Money Sent'
    MONEY_RECEIVED = 'MONEY_RECEIVED', 'Money Received'

    @classmethod
    def outgoing_types(cls):
        return (
            cls.MONEY_SENT,
        )

    @classmethod
    def incoming_types(cls):
        return (
            cls.MONEY_RECEIVED,
        )