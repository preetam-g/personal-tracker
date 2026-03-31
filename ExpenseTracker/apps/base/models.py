from collections import Counter

from django.db import models, transaction
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, **kwargs):
        """
        Does cascade delete on the children.
        """
        total = 0
        res = Counter()

        for obj in self.all():
            result = obj.delete(**kwargs)
            if result:
                c, b = result
                total += c
                res.update(b)

        return total, dict(res)

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

    SOFT_DELETE_CASCADES = ()

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager() # to ensure all_objects.delete also triggers soft delete

    class Meta:
        abstract = True # to avoid creating a table in DB

    def delete(self, **kwargs):
        """This performs soft delete."""
        if self.is_deleted: return 0, {}

        total_deleted = 0
        deleted_details = Counter()

        with transaction.atomic():

            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()

            model_name = self._meta.label
            total_deleted += 1
            deleted_details[model_name] += 1

            for rel_name in getattr(self, 'SOFT_DELETE_CASCADES', ()):
                related_attr = getattr(self, rel_name, None)
                if related_attr is None: continue

                if hasattr(related_attr, 'all'):
                    t, r = related_attr.all().delete(**kwargs)
                    total_deleted += t
                    deleted_details.update(r)

                elif hasattr(related_attr, 'delete'):
                    result = related_attr.delete(**kwargs)
                    if result:
                        t, r = result
                        total_deleted += t
                        deleted_details.update(r)

            return total_deleted, dict(deleted_details)

    def hard_delete(self, **kwargs):
        """Completely deletes the records."""
        super().delete(**kwargs)

    def restore(self):
        """Restore soft deleted records."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()