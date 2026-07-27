from django.db import models


class HabitQuerySet(models.QuerySet):

    def all_for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_active=True)


class HabitPlanQuerySet(models.QuerySet):

    def all_for_user(self, user):
        return self.filter(user=user)


class DailyProgressQuerySet(models.QuerySet):

    def all_for_user(self, user):
        return self.filter(user=user)