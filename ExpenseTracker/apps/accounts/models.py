from django.contrib.auth.models import AbstractUser
from apps.base.models import SoftDeleteModel
from django.utils import timezone
import datetime


class UserProfile(AbstractUser, SoftDeleteModel):

    class Meta:
        ordering = ['-date_joined']