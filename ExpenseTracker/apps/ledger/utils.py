from django.db import models

class LoanType(models.TextChoices):
    LENT = 'lent', 'Lent'
    BORROWED = 'borrowed', 'Borrowed'

class LinkStatus(models.TextChoices):
    UNLINKED = 'unlinked', 'Unlinked'
    PENDING = 'pending', 'Pending'
    LINKED = 'confirmed', 'Confirmed'