from django.db import models


class Currency(models.Model):

    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('code',)
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"


class ExchangeRate(models.Model):

    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='base_exchange_rates',
    )

    target_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='target_exchange_rates',
    )

    rate = models.DecimalField(max_digits=20, decimal_places=10)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['base_currency', 'target_currency'],
                name='unique_currency_pair',
            ),
        ]

    def __str__(self):
        return f"{self.base_currency} --> {self.target_currency}: {self.rate}"