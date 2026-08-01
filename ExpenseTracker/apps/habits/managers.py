from django.db import models
from django.db.models import Q

class HabitQuerySet(models.QuerySet):

    def for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_active=True)


class HabitPlanQuerySet(models.QuerySet):

    def with_habit(self):
        return self.select_related('habit')

    def for_user(self, user):
        return self.filter(habit__user=user)


class DailyProgressQuerySet(models.QuerySet):

    def with_plan(self):
        return self.select_related('plan', 'plan__habit')

    def for_user(self, user):
        return self.filter(plan__habit__user=user)