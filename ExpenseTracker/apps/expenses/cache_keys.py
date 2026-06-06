
EXPENSES_PREFIX = "expenses"
# EXPENSES_VERSION = "v1" # use later


def home(user_id: int) -> str:
    return f"{EXPENSES_PREFIX}:home:{user_id}"


def dashboard(user_id: int, start_date: str, end_date: str) -> str:
    return (
        f"{EXPENSES_PREFIX}:dashboard:"
        f"{user_id}:{start_date}:{end_date}"
    )