# read/query logic
from apps.forex.models import Currency, ExchangeRate


def get_currency_by_code(code: str) -> Currency | None:

    return Currency.objects.filter(
        code=code,
        is_active=True,
    ).first()


def get_exchange_rate_record(base_code: str, target_code: str) -> ExchangeRate | None:

    return ExchangeRate.objects.filter(
        base_currency__code=base_code,
        target_currency__code=target_code,
    ).first()