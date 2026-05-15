from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField
from django.db.models.functions import Lower

from apps.base.models import SoftDeleteModel, TimeStampedModel
from core import settings
from .utils import LinkStatus, TransactionType


class Contact(SoftDeleteModel, TimeStampedModel):

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    # if any user link to contact
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_as"
    )

    # consent state
    link_status = models.CharField(
        max_length=20,
        choices=LinkStatus.choices,
        default=LinkStatus.UNLINKED,
    )

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'owner',
                condition=models.Q(is_deleted=False),
                name='unique_%(class)s_per_user_insensitive',
            )
        ]

    def get_balance(self):
        """
        Calculates the running balance.
        """
        result = self.transactions.aggregate(
            balance=Sum(
                Case(
                    # If it's a positive transaction type, use the positive amount
                    When(
                        type__in=[TransactionType.LENT, TransactionType.PAYMENT_SENT],
                        then=F('amount')
                    ),
                    # Otherwise, make the amount negative
                    default=-F('amount'),
                    output_field=DecimalField()
                )
            )
        )
        return result['balance'] or 0

    def __str__(self):
        return self.name


class Transaction(SoftDeleteModel, TimeStampedModel):

    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='transactions'
    )

    amount = models.DecimalField(decimal_places=2, max_digits=10)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    date = models.DateField()
    note = models.TextField(null=True, blank=True, max_length=100)

    class Meta:
        ordering = ('-date', '-created_at')

    def clean(self):
        super().clean()
        if self.amount and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be strictly positive."})

    @property
    def signed_amount(self):
        """
        Returns the amount with the correct mathematical sign. Positive when User is owed money.
        Useful for iterating over transactions in a template to show a running tally.
        """
        if self.type in [TransactionType.LENT, TransactionType.PAYMENT_SENT]:
            return self.amount
        return -self.amount

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} on {self.date}"