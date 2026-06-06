
EXPENSES_PREFIX = "expenses"
# EXPENSES_VERSION = "v1" # use later


def home(user_id: int) -> str:
    return f"{EXPENSES_PREFIX}:user:{user_id}:home"


def dashboard(user_id: int, timeframe: str, today_date: str) -> str:
    return (
        f"{EXPENSES_PREFIX}:user:{user_id}:"
        f"dashboard:{timeframe}:{today_date}"
    )