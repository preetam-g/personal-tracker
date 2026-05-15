from django.db import models
from django.db.models.functions import Lower

from apps.base.models import SoftDeleteModel
from core import settings
from .utils import LoanType, LinkStatus


class Contact(SoftDeleteModel):

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
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
        null=False,
        blank=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class Loan(SoftDeleteModel):

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='loans')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')

    amount = models.DecimalField(decimal_places=2, max_digits=10, null=False, blank=False)
    type = models.CharField(
        choices=LoanType.choices,
        # default=LoanType.LENT,
        null=False,
        blank=False,
    )
    note = models.TextField(null=True, blank=True, max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payments(SoftDeleteModel):

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(decimal_places=2, max_digits=10, null=False, blank=False)
    note = models.TextField(null=True, blank=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)