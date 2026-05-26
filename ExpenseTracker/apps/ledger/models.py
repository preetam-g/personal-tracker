from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField
from django.db.models.functions import Lower

from apps.base.models import SoftDeleteModel, TimeStampedModel
from core import settings
from .managers import TransactionManager, ContactManager
from .utils import LinkStatus, TransactionType


class Contact(SoftDeleteModel, TimeStampedModel):

    objects = ContactManager()

    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_as"
    )

    link_status = models.CharField(
        max_length=20,
        choices=LinkStatus.choices,
        default=LinkStatus.UNLINKED,
    )

    class Meta:
        ordering = ('name', 'user')
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'user',
                condition=models.Q(is_deleted=False),
                name='unique_%(class)s_per_user_insensitive',
            )
        ]

    def __str__(self):
        return self.name


class Transaction(SoftDeleteModel, TimeStampedModel):

    objects = TransactionManager()

    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    amount = models.DecimalField(decimal_places=2, max_digits=10)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    date = models.DateTimeField()
    note = models.TextField(null=True, blank=True, max_length=50)

    class Meta:
        ordering = ('-date', '-created_at')

    def clean(self):
        super().clean()
        if self.amount and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be strictly positive."})

    @property
    def signed_amount(self):
        """
        Returns the amount with the correct mathematical sign. Positive when User receives money.
        Used in templates to display amount accordingly.
        """
        if self.type in TransactionType.incoming_types():
            return self.amount
        return -self.amount

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} on {self.date}"