from django.conf import settings
from django.db import models
from .managers import ExpenseManager


class ExpenseCategory(models.Model): # grocery, shopping, ...
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ExpenseType(models.Model): # upi, credit card, ...
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Expense(models.Model):

    objects = models.Manager()
    browser = ExpenseManager() # .browser will use custom manager

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    note = models.CharField(blank=True, max_length=20)

    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(ExpenseType, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.amount}({self.note}) on {self.date.date}"