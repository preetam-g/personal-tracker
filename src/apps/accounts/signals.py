from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.forex.models import Currency

from .models import UserPreference


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_preference(sender, instance, created, **kwargs):

    if not created:
        return

    inr = Currency.objects.get(code='INR')

    UserPreference.objects.create(
        user=instance,
        preferred_currency=inr,
    )