
LEDGER_PREFIX = "ledger"


def home(user_id: int, timeframe: str, today_date: str) -> str:
    return f"{LEDGER_PREFIX}:user:{user_id}:home:{timeframe}:{today_date}"