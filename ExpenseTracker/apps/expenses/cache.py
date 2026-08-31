from django.core.cache import cache

APP = "expenses"

def home_key(user_id):
    return f"{APP}:home:user:{user_id}:"

def summary_key(user_id, date, timeframe):
    return f"{APP}:summary:user:{user_id}:date:{date}:timeframe:{timeframe}:"

def invalidate_cache(user_id, obj):
    return cache.delete_pattern(
        f"{APP}:*:user:{user_id}*:"
    )