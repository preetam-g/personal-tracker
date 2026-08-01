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