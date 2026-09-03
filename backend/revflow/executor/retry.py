"""
RevFlow Executor — Real retry via Razorpay Test Mode.

Per §3.2, §8.3: Only this module touches a payment rail.
Returns typed RetryResult, never raises.
"""
from revflow.adapters.razorpay_client import get_razorpay_adapter, RetryResult
from revflow.ingestion.normaliser import Event


async def execute_retry_now(event: Event) -> RetryResult:
    """
    Execute retry_now for an event.

    Per §8.3: Wraps Razorpay call with try/except, max 3 attempts with backoff.
    Network/auth/5xx → api_error. Genuine decline → failed.
    """
    adapter = get_razorpay_adapter()
    return await adapter.attempt_recovery(event)