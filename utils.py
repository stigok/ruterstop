from datetime import datetime, timedelta
from functools import wraps, _make_key


def timed_cache(*, expires_sec=60, now=datetime.now):
    """
    Decorator function to cache function calls with same signature for a set
    amount of time.

    It does not delete any keys from the cache, so it might grow indefinitely.
    """
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*_args, **_kwargs):
            time = now()
            key = _make_key(_args, _kwargs, False) # pylint: disable=protected-access

            if key not in cache or time > cache[key]["timestamp"] + timedelta(seconds=expires_sec):
                cache[key] = dict(value=func(*_args, **_kwargs), timestamp=time)

            return cache[key]["value"]

        return wrapper

    return decorator
