from __future__ import annotations


class DeepSeekClientError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class DeepSeekAuthError(DeepSeekClientError):
    pass


class DeepSeekBillingError(DeepSeekClientError):
    pass


class DeepSeekUnavailableError(DeepSeekClientError):
    pass


class DeepSeekInvalidResponseError(DeepSeekClientError):
    pass
