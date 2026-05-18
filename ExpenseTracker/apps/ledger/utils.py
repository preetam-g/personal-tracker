from django.db import models

class TransactionType(models.TextChoices):
    BORROWED = 'BORROWED', 'Borrowed'
    LENT = 'LENT', 'Lent'
    PAYMENT_SENT = 'PAYMENT_SENT', 'Payment Sent'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'

class LinkStatus(models.TextChoices):
    UNLINKED = 'unlinked', 'Unlinked'
    PENDING = 'pending', 'Pending'
    LINKED = 'confirmed', 'Confirmed'