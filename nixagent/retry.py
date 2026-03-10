import time
import requests
from typing import Callable, Any, Optional
from .logger import logger

# HTTP status codes that are worth retrying (transient errors)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# HTTP status codes that are fatal — retrying won't help
FATAL_STATUS_CODES = {400, 401, 403, 404, 422}


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def call_with_retry(
    fn: Callable,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Calls `fn(*args, **kwargs)` with exponential backoff retry logic.

    Args:
        fn:             The callable to execute (e.g. a provider's call function).
        max_retries:    Maximum number of retry attempts after the first failure.
        retry_delay:    Initial delay in seconds between retries.
        backoff_factor: Multiplier applied to the delay after each retry.
        *args / **kwargs: Arguments forwarded to `fn`.

    Returns:
        The return value of `fn` on success.

    Raises:
        RetryError: When all retries are exhausted.
        Exception:  Any fatal (non-retryable) exception from `fn`.
    """
    last_exc = None
    delay = retry_delay

    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None

            # Fatal errors — don't retry
            if status_code in FATAL_STATUS_CODES:
                logger.error(f"[Retry] Fatal HTTP {status_code} — not retrying: {e}")
                raise

            # Retryable HTTP error
            if status_code in RETRYABLE_STATUS_CODES:
                last_exc = e
                if attempt < max_retries:
                    logger.warning(
                        f"[Retry] HTTP {status_code} on attempt {attempt + 1}/{max_retries + 1}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
                    continue

            # Unknown HTTP error — raise immediately
            raise

        except requests.exceptions.Timeout as e:
            last_exc = e
            if attempt < max_retries:
                logger.warning(
                    f"[Retry] Request timed out on attempt {attempt + 1}/{max_retries + 1}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise RetryError(
                    f"LLM call timed out after {max_retries + 1} attempts.", last_exc
                )

        except requests.exceptions.ConnectionError as e:
            last_exc = e
            if attempt < max_retries:
                logger.warning(
                    f"[Retry] Connection error on attempt {attempt + 1}/{max_retries + 1}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                raise RetryError(
                    f"LLM call failed with connection error after {max_retries + 1} attempts.", last_exc
                )

        except Exception as e:
            # Non-requests exceptions (e.g., JSON parse errors) — raise immediately
            raise

    # Should never reach here, but be safe
    raise RetryError(
        f"LLM call failed after {max_retries + 1} attempts.", last_exc
    )
