from django.db import models

class TransactionType(models.TextChoices):
    # Positive impact on balance (Contact owes User more)
    LENT = 'LENT', 'Lent'
    PAYMENT_SENT = 'PAYMENT_SENT', 'Payment Sent'

    # Negative impact on balance (Contact owes User less / User owes Contact)
    BORROWED = 'BORROWED', 'Borrowed'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'

class LinkStatus(models.TextChoices):
    UNLINKED = 'unlinked', 'Unlinked'
    PENDING = 'pending', 'Pending'
    LINKED = 'confirmed', 'Confirmed'