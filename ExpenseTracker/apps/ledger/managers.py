from django.contrib.auth.base_user import AbstractBaseUser

from apps.base.models import SoftDeleteManager, SoftDeleteQuerySet


class TransactionManager(SoftDeleteManager):

    def base_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.get_queryset().filter(user=user)

    def all_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.base_for_user(user).select_related('contact')


class ContactManager(SoftDeleteManager):

    def base_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return self.get_queryset().filter(owner=user)

    def all_for_user(self, user:AbstractBaseUser) -> SoftDeleteQuerySet:
        return (
            self.base_for_user(user)
            .select_related('owner', 'linked_user')
            .only(
                'id', 'amount', 'date', 'note', 'type',
                'contact__name',
            )
        )