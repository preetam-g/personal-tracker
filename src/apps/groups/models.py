from django.db import models
from django.utils import timezone
from core import settings
from apps.base.models import TimeStampedModel


class SharedGroup(TimeStampedModel):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_shared_groups',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='GroupMembership',
        related_name='shared_groups',
    )

    def __str__(self):
        return self.name


class GroupMembership(TimeStampedModel):
    group = models.ForeignKey(SharedGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'user'], name='unique_shared_group_member')]


class SharedBill(TimeStampedModel):
    group = models.ForeignKey(SharedGroup, on_delete=models.CASCADE, related_name='bills')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='paid_shared_bills')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_shared_bills')
    category = models.ForeignKey(
        'expenses.ExpenseCategory', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='shared_bills',
    )

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='shared_bill_amount_positive')]

    def __str__(self):
        return self.title


class BillShare(models.Model):
    bill = models.ForeignKey(SharedBill, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['bill', 'user'], name='unique_shared_bill_participant'),
            models.CheckConstraint(condition=models.Q(percentage__gt=0) & models.Q(percentage__lte=100), name='shared_bill_percentage_range'),
            models.CheckConstraint(condition=models.Q(amount__gte=0), name='shared_bill_share_nonnegative'),
        ]


class GroupPayment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Waiting for receiver'
        AUTO_APPROVED = 'autoapproved', 'Automatically approved'
        CONFIRMED = 'confirmed', 'Settled'
        REJECTED = 'rejected', 'Rejected'

    group = models.ForeignKey(SharedGroup, on_delete=models.CASCADE, related_name='payments')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='shared_payments_sent')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='shared_payments_received')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_shared_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AUTO_APPROVED)
    payment_reference = models.CharField(max_length=64, blank=True)
    payee_upi_id = models.CharField(max_length=255, blank=True)
    payee_name = models.CharField(max_length=99, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='shared_payment_amount_positive'),
            models.CheckConstraint(condition=~models.Q(from_user=models.F('to_user')), name='shared_payment_distinct_people'),
            models.UniqueConstraint(
                fields=['group', 'from_user', 'payment_reference'],
                condition=~models.Q(payment_reference=''), name='unique_group_payment_claim',
            ),
        ]
