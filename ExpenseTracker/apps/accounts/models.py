from django.contrib.auth.models import AbstractUser
from apps.base.models import SoftDeleteModel


class UserProfile(AbstractUser, SoftDeleteModel):

    class Meta:
        ordering = ['-date_joined']