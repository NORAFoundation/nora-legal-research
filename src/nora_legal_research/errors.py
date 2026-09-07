from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


PROVIDER_ERROR_CODES = {
    "PROVIDER_ERROR",
    "PROVIDER_UNAVAILABLE",
    "PROVIDER_AUTHENTICATION_ERROR",
    "PROVIDER_RATE_LIMITED",
    "PROVIDER_CONTRACT_ERROR",
    "PROVIDER_PARTIAL_RESULT",
    "UNSUPPORTED_PROVIDER_CAPABILITY",
}


class ProviderErrorInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    retryable: bool = False
    http_status: Optional[int] = None
    access_mode: Optional[str] = None

    @field_validator("code")
    @classmethod
    def known_code(cls, value: str) -> str:
        if value not in PROVIDER_ERROR_CODES:
            raise ValueError("unknown provider error code")
        return value


class ProviderErrorEnvelope(BaseModel):
    """Redacted, machine-readable failure vector; never contains raw payloads."""

    model_config = ConfigDict(extra="forbid")

    provider_contract_version: int
    provider_name: str
    research_id: str
    error: ProviderErrorInfo


class ProviderError(RuntimeError):
    code = "PROVIDER_ERROR"
    retryable = False

    def __init__(self, message: str = "provider request failed", *, http_status: int | None = None, access_mode: str | None = None):
        super().__init__(message)
        self.info = ProviderErrorInfo(
            code=self.code,
            retryable=self.retryable,
            http_status=http_status,
            access_mode=access_mode,
        )


class ProviderUnavailable(ProviderError):
    code = "PROVIDER_UNAVAILABLE"
    retryable = True


class ProviderAuthenticationError(ProviderError):
    code = "PROVIDER_AUTHENTICATION_ERROR"


class ProviderRateLimited(ProviderError):
    code = "PROVIDER_RATE_LIMITED"
    retryable = True


class ProviderContractError(ProviderError):
    code = "PROVIDER_CONTRACT_ERROR"


class ProviderPartialResult(ProviderError):
    code = "PROVIDER_PARTIAL_RESULT"
    retryable = True


class UnsupportedProviderCapability(ProviderError):
    code = "UNSUPPORTED_PROVIDER_CAPABILITY"
