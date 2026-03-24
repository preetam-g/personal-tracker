from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Ensures that we only fetch non-deleted records.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """
    Base model for all soft-deleted records. The records will stay in database.
    Deleted records will have a boolean flag set to True with a timestamp.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

