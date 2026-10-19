from django.core.validators import RegexValidator, URLValidator


validate_upi_id = RegexValidator(
    regex=r'\A[a-zA-Z0-9._-]{2,}@[a-zA-Z0-9.-]{2,}\Z',
    message='Enter a valid UPI ID, for example yourname@bank.',
)


# Compatibility symbol for the already-applied historical migration 0009 only.
# Current profile models and forms have no hosted-payment-link field.
validate_toropay_link = URLValidator(schemes=['https'])
