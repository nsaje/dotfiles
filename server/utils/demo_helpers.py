import functools
import datetime


def demo_accounts_latest_success_now(demo_accounts):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            now = datetime.datetime.now()
            for account in demo_accounts:
                result[account.id] = now
            return result
        return wrapper
    return decorator
