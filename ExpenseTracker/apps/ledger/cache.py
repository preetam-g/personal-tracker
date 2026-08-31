from django.core.cache import cache

APP = "ledger"

def home_key(user_id, timeframe):
    return f"{APP}:home:user:{user_id}:timeframe:{timeframe}:"

def summary_key(user_id):
    return f"{APP}:summary:user:{user_id}:"

def invalidate_cache(user_id, obj=None):
    return cache.delete_pattern(
        f"{APP}:*:user:{user_id}:*"
    )