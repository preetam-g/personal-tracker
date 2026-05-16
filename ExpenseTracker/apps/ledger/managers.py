from django.contrib.auth.base_user import AbstractBaseUser

from apps.base.models import SoftDeleteManager, SoftDeleteQuerySet


class TransactionManager(SoftDeleteManager):

    def get_queryset(self):
        return super().get_queryset().select_related('contact')

    def all_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.get_queryset().filter(user=user)