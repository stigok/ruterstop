import re

from datetime import datetime, timedelta
from functools import wraps, _make_key


def norwegian_ascii(unicode_str):
    """
    Return an ASCII string with Norwegian chars replaced with their closest
    ASCII representation. Other non-ASCII characters are ignored and removed.
    """
    unicode_str = re.sub(r"ø", "oe", unicode_str, flags=re.IGNORECASE)
    unicode_str = re.sub(r"æ", "ae", unicode_str, flags=re.IGNORECASE)
    unicode_str = re.sub(r"å", "aa", unicode_str, flags=re.IGNORECASE)
    return unicode_str.encode("ascii", "ignore").decode()


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
            key = _make_key(_args, _kwargs, False)  # pylint: disable=protected-access

            if key not in cache or time > cache[key]["timestamp"] + timedelta(
                seconds=expires_sec
            ):
                cache[key] = dict(value=func(*_args, **_kwargs), timestamp=time)

            return cache[key]["value"]

        return wrapper

    return decorator


def delta(until=None, *, since=None):
    """
    Return amount of whole minutes until `until` date occurs, since `since`.
    Returns -1 if `since` is later than `until`.
    """
    if not since:
        since = datetime.now()

    if since > until:
        return -1

    secs = (until - since).seconds
    mins = max(0, secs / 60)
    return int(mins)


def human_delta(until=None, *, since=None):
    """
    Return a 6 char long string describing minutes left 'until' date occurs.
    Example output:
       naa (if delta < 60 seconds)
     1 min
     7 min
    10 min
    99 min
    """
    now_str = "{:>6}".format("naa")

    since = since if since else datetime.now()
    mins = min(delta(until, since=since), 99)

    if mins < 1:
        return now_str

    return "{:2} min".format(mins)
