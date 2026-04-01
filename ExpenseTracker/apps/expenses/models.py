from django.conf import settings
from django.db import models
from django.utils import timezone
from .managers import ExpenseManager
from apps.base.models import SoftDeleteModel


class ExpenseCategory(SoftDeleteModel): # grocery, shopping, ...
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseType(SoftDeleteModel): # upi, credit card, ...
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(SoftDeleteModel):

    browser = ExpenseManager() # .browser will use custom manager

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')

    date = models.DateTimeField(null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    note = models.CharField(blank=True, max_length=50)

    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(ExpenseType, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f"{self.amount} on {timezone.localdate(self.date)}"