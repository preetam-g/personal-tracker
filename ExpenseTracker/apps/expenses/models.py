from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from .managers import ExpenseManager, CategoryTypeManager
from apps.base.models import SoftDeleteModel, TimeStampedModel


class BaseCategoryType(SoftDeleteModel, TimeStampedModel):

    name = models.CharField(max_length=50)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_items"
    )

    objects = CategoryTypeManager()

    class Meta:
        abstract = True
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                'user',
                condition=models.Q(is_deleted=False),
                name='unique_%(class)s_per_user_case_insensitive'
            )
        ]

    def clean(self):
        if not self.name:
            return

        name = self.name.strip()

        is_exists = self.__class__.objects.filter(
            models.Q(user__isnull=True) | models.Q(user=self.user),
            name__iexact=name,
            is_deleted=False
        ).exclude(pk=self.pk).exists()

        if is_exists:
            raise ValidationError(
                f"This {self._meta.verbose_name} already exists"
            )

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ExpenseCategory(BaseCategoryType):
    class Meta(BaseCategoryType.Meta):
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"


class ExpenseType(BaseCategoryType):
    class Meta(BaseCategoryType.Meta):
        verbose_name = "Expense Type"
        verbose_name_plural = "Expense Types"


class Expense(SoftDeleteModel, TimeStampedModel):

    browser = ExpenseManager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')

    date = models.DateTimeField(null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    note = models.CharField(blank=True, max_length=50)

    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(ExpenseType, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:

        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['is_deleted']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name='amount_positive',
            )
        ]

    def __str__(self):
        return f"{self.amount}, {timezone.localdate(self.date)} ({self.user.username})"

    def clean(self):

        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': "Amount must be greater than 0."})