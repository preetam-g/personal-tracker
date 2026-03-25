from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def restore(self):
        return super().update(is_deleted=False, deleted_at=None)

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Ensures that we only fetch non-deleted records."""
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Includes all records, but safely uses the SoftDeleteQuerySet."""
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Base model for all soft-deleted records. The records will stay in database.
    Deleted records will have a boolean flag set to True with a timestamp.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager() # to ensure all_objects.delete also triggers soft delete

    class Meta:
        abstract = True # to avoid creating a table in DB

    def delete(self, **kwargs):
        """This performs soft delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, **kwargs):
        """Completely deletes the records."""
        super().delete(**kwargs)

    def restore(self):
        """Restore soft deleted records."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()