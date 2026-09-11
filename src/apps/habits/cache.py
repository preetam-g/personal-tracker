from django.core.cache import cache as django_cache
from . import models

APP = "habits"


def home_progresses_key(user_id, date):
    return (
        f"{APP}:home:progresses:"
        f"user:{user_id}:"
        f"date:{date}:"
    )

def home_trend_key(user_id, date):
    return (
        f"{APP}:home:trend:"
        f"user:{user_id}:"
        f"date:{date}:"
    )


def manage_habits_key(user_id):
    return (
        f"{APP}:manage:habits:"
        f"user:{user_id}:"
    )

def manage_goals_key(user_id):
    return (
        f"{APP}:manage:goals:"
        f"user:{user_id}:"
    )


def history_key(user_id):
    return (
        f"{APP}:history:"
        f"user:{user_id}:"
    )

def details_key(user_id, plan_id):
    return (
        f"{APP}:details:"
        f"user:{user_id}:"
        f"plan:{plan_id}:"
    )


def invalidate_cache(user_id, obj):

    if isinstance(obj, models.Habit):
        return django_cache.delete(
            manage_habits_key(user_id)
        )

    if isinstance(obj, models.HabitPlan):
        return django_cache.delete_many([
            manage_goals_key(user_id),
            history_key(user_id),
            details_key(user_id, obj.id),
        ])

    if isinstance(obj, models.DailyProgress):
        deleted = django_cache.delete_pattern(
            f"{APP}:home:*:user:{user_id}:*"
        )
        deleted += django_cache.delete(
            details_key(user_id, obj.plan.id)
        )
        return deleted

    return django_cache.delete_pattern(
        f"{APP}:*:user:{user_id}:*"
    )