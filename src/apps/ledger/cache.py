from django.core.cache import cache

APP = "ledger"

def home_key(user_id, date):
    return (
        f"{APP}:home:"
        f"user:{user_id}:"
        f"date:{date}:"
    )

def summary_key(user_id):
    return (
        f"{APP}:summary:"
        f"user:{user_id}:"
    )

def invalidate_cache(user_id, obj=None):
    return cache.delete_pattern(
        f"{APP}:*:user:{user_id}:*"
    )