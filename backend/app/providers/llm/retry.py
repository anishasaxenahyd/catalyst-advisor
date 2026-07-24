"""Small synchronous retry helper shared by vendor provider implementations.

Generic on purpose — any provider that wants exponential-backoff retry over
a set of exception types it considers transient can reuse this rather than
hand-rolling a loop.
"""

import logging
import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

logger = logging.getLogger("catalyst.llm")

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 6.0


def call_with_retries(
    fn: Callable[[], T],
    *,
    retryable: tuple[type[Exception], ...],
    config: RetryConfig,
    op_name: str,
) -> T:
    """Calls `fn()`, retrying with exponential backoff + jitter on any
    exception type listed in `retryable`. Any other exception propagates
    immediately on the first attempt — retrying a non-transient failure
    (bad API key, malformed request) just wastes time and quota."""

    last_exc: Exception | None = None
    for attempt in range(1, config.max_attempts + 1):
        try:
            return fn()
        except retryable as exc:
            last_exc = exc
            if attempt == config.max_attempts:
                break
            delay = min(config.max_delay_seconds, config.base_delay_seconds * (2 ** (attempt - 1)))
            delay += random.uniform(0, 0.25)
            logger.warning(
                "%s attempt %d/%d failed (%s: %s); retrying in %.2fs",
                op_name, attempt, config.max_attempts, type(exc).__name__, exc, delay,
            )
            time.sleep(delay)

    assert last_exc is not None
    logger.error("%s exhausted %d attempts, giving up: %s", op_name, config.max_attempts, last_exc)
    raise last_exc
