from django.contrib.auth.models import AbstractUser
from django.db import models

class UserProfile(AbstractUser):

    class Meta:
        ordering = ['-date_joined']