from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from core import settings

from apps.base.models import TimeStampedModel

from .managers import (
    TransactionQuerySet,
    ContactQuerySet,
    TransactionSettlementQuerySet
)
from .utils import TransactionType


class Contact(TimeStampedModel):

    objects = ContactQuerySet.as_manager()

    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    class Meta:
        ordering = ('name', 'user')
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'user',
                name='unique_%(class)s_per_user_insensitive',
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.name: return

        name = self.name.strip()
        is_exists = self.__class__.objects.filter(
            user=self.user,
            name__iexact=name,
        ).exclude(pk=self.pk).exists()

        if is_exists:
            raise ValidationError({
                'name': f"A similar contact with name '{name}' already exists.",
            })


class Transaction(TimeStampedModel):

    objects = TransactionQuerySet.as_manager()

    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='transactions'
    )

    amount = models.DecimalField(decimal_places=2, max_digits=10)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    date = models.DateTimeField()
    note = models.TextField(null=True, blank=True, max_length=50)

    is_settled = models.BooleanField(default=False)
    settlement = models.ForeignKey(
        'TransactionSettlement',
        on_delete=models.PROTECT,
        related_name='transactions',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ('-date', '-created_at')

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
        return (f"{self.contact}-{self.get_type_display()}: "
                f"{self.amount} on {timezone.localdate(self.date)}")

    @property
    def can_be_deleted(self):
        return (
            not self.is_settled
            and not hasattr(self, "carry_forward_settlement")
        )

    @property
    def can_be_edited(self):
        return (
            not self.is_settled
            and not hasattr(self, "carry_forward_settlement")
        )


class TransactionSettlement(TimeStampedModel):

    objects = TransactionSettlementQuerySet.as_manager()

    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='settlements'
    )

    carry_forward_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        related_name='carry_forward_settlement',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ('-created_at',)