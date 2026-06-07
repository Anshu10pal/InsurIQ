import functools
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


def retry_openai(func):
    """
    Decorator for OpenAI API calls.
    - 1 attempt only (fail fast — was 3, reduced to avoid 56-second waits)
    - Exponential backoff min=1s max=2s (was min=2 max=10)
    """
    @retry(
        stop=stop_after_attempt(1),
        wait=wait_exponential(min=1, max=2),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def retry_db(func):
    """
    Decorator for database calls.
    Same fail-fast config as retry_openai.
    """
    @retry(
        stop=stop_after_attempt(1),
        wait=wait_exponential(min=1, max=2),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
