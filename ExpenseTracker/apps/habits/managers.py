from django.db import models


class HabitManager(models.Manager):

    def all_for_user(self, user):
        return self.get_queryset().filter(user=user)


class HabitPlanManager(models.Manager):

    def all_for_user(self, user):
        return self.get_queryset().filter(user=user)


class DailyProgressManager(models.Manager):

    def all_for_user(self, user):
        return self.get_queryset().filter(user=user)