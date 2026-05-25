# business logic ( modify DB, call APIs )

from django.conf import settings
from django.db import transaction
from django.utils import timezone

import requests
from decimal import Decimal
import logging

from .models import Currency, ExchangeRate
from .utils import ResultType, CACHE_DURATION
from .exceptions import (
    ExchangeRateAPIError,
    ExchangeRateAPIResponseError,
    ExchangeRateUnavailable
)
from .selectors import get_exchange_rate_record, get_currency_by_code

logger = logging.getLogger(__name__)


def fetch_latest_exchange_rates(base_currency_code: str) -> dict:

    base_url = settings.EXCHANGE_RATE_BASE_URL
    api_key = settings.EXCHANGE_RATE_API_KEY

    if not (base_url and api_key):

        logger.error("ExchangeRate API configuration is missing")

        raise ExchangeRateAPIError("ExchangeRate API configuration is missing.")

    url = f"{base_url}/{api_key}/latest/{base_currency_code}"

    logger.info(
        f"Fetching latest exchange rates "
        f"for {base_currency_code}"
    )

    try:
        response = requests.get(url, timeout=settings.EXCHANGE_RATE_API_TIMEOUT)
        response.raise_for_status() # raise exception for 4xx/5xx responses
    except requests.RequestException as exc:

        logger.exception(
            f"Failed to communicate with "
            f"ExchangeRate API for "
            f"{base_currency_code}"
        )

        raise ExchangeRateAPIError(
            "Failed to communicate with ExchangeRate API."
        ) from exc

    data = response.json()
    if data.get('result') == ResultType.ERROR.value:

        logger.error(
            f"ExchangeRate API returned error "
            f"for {base_currency_code}: "
            f"{data.get('error-type')}"
        )

        raise ExchangeRateAPIResponseError(
            f"Failed to fetch latest exchange rates. "
            f"Error Type: {data['error-type']}"
        )

    logger.info(
        f"Successfully fetched exchange rates "
        f"for {base_currency_code}"
    )

    return data


@transaction.atomic
def sync_latest_rates(base_currency_code: str) -> None:

    base_currency_code = base_currency_code.strip().upper()

    logger.info(
        f"Syncing latest exchange rates "
        f"for {base_currency_code}"
    )

    data = fetch_latest_exchange_rates(base_currency_code)
    conversion_rates = data.get("conversion_rates", {})

    currencies = {
        currency.code: currency
        for currency in Currency.objects.filter(is_active=True)
    } # preload all currency objects
    base_curr = currencies.get(base_currency_code)

    if not base_curr:

        logger.error(
            f"Base currency "
            f"{base_currency_code} "
            f"not found."
        )

        raise ExchangeRateUnavailable(
            f"Base currency "
            f"{base_currency_code} "
            f"not found."
        )

    updated_count = 0
    for (target_curr_code, rate) in conversion_rates.items():

        target_curr = currencies.get(target_curr_code)
        if not target_curr:
            continue

        ExchangeRate.objects.update_or_create(
            base_currency=base_curr,
            target_currency=target_curr,
            defaults={
                "rate": Decimal(str(rate)),
            }
        )

        updated_count += 1

    logger.info(
        f"Successfully synced "
        f"{updated_count} exchange rates "
        f"for {base_currency_code}"
    )


def get_exchange_rate(from_code: str, to_code: str) -> Decimal:

    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()

    logger.info(
        f"Getting exchange rate: "
        f"{from_code} -> {to_code}"
    )

    from_curr_exists = get_currency_by_code(from_code)
    if not from_curr_exists:
        logger.warning(
            f"Invalid base currency code: "
            f"{from_code}"
        )
        raise ExchangeRateUnavailable(
            f"Invalid currency code: {from_code}"
        )

    to_curr_exists = get_currency_by_code(to_code)
    if not to_curr_exists:
        logger.warning(
            f"Invalid target currency code: "
            f"{to_code}"
        )
        raise ExchangeRateUnavailable(
            f"Invalid currency code: {to_code}"
        )

    if from_code == to_code:
        logger.info(
            f"Same currency conversion: "
            f"{from_code} -> {to_code}"
        )
        return Decimal('1.0')

    exchange_rate = get_exchange_rate_record(from_code, to_code)

    if not exchange_rate: # record not in DB
        logger.info(
            f"Exchange rate missing in DB: "
            f"{from_code} -> {to_code}. "
            f"Syncing latest rates."
        )
        sync_latest_rates(from_code)
        exchange_rate = get_exchange_rate_record(from_code, to_code)

    elif (timezone.now() - exchange_rate.fetched_at) > CACHE_DURATION: # record is old
        logger.info(
            f"Exchange rate cache stale: "
            f"{from_code} -> {to_code}. "
            f"Refreshing rates."
        )
        sync_latest_rates(from_code)
        exchange_rate.refresh_from_db()

    if not exchange_rate:
        logger.error(
            f"Exchange rate unavailable: "
            f"{from_code} -> {to_code}"
        )
        raise ExchangeRateUnavailable(
            f"Exchange rate unavailable for "
            f"{from_code} -> "
            f"{to_code}"
        )

    logger.info(
        f"Exchange rate fetched successfully: "
        f"{from_code} -> {to_code} = "
        f"{exchange_rate.rate}"
    )

    return exchange_rate.rate


def convert_currency(from_code: str, to_code: str, amount) -> Decimal:

    logger.info(
        f"Converting currency: "
        f"{amount} "
        f"{from_code} -> {to_code}"
    )

    rate = get_exchange_rate(from_code, to_code)
    amt = Decimal(str(amount))
    converted_amt = rate * amt

    logger.info(
        f"Conversion successful: "
        f"{amount} ({from_code}) = "
        f"{converted_amt} ({to_code})"
    )

    return converted_amt.quantize(Decimal('0.01'))