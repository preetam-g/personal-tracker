from enum import Enum
from datetime import timedelta


CACHE_DURATION = timedelta(hours=12)


class ResultType(Enum):
    SUCCESS = "success"
    ERROR = "error"