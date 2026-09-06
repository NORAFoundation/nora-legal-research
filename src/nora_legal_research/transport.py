from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .provider_contract import ProviderSearchRequestModel, ProviderSearchResponseModel
from .providers import AuthorityResearchRequest, ProviderCapabilities, ProviderSearchResult


class ProviderError(RuntimeError):
    code = "PROVIDER_ERROR"


class ProviderUnavailable(ProviderError):
    code = "PROVIDER_UNAVAILABLE"


class ProviderAuthenticationError(ProviderError):
    code = "PROVIDER_AUTHENTICATION_ERROR"


class ProviderRateLimited(ProviderError):
    code = "PROVIDER_RATE_LIMITED"


class ProviderContractError(ProviderError):
    code = "PROVIDER_CONTRACT_ERROR"


class ProviderPartialResult(ProviderError):
    code = "PROVIDER_PARTIAL_RESULT"


class UnsupportedProviderCapability(ProviderError):
    code = "UNSUPPORTED_PROVIDER_CAPABILITY"


class AuthorityProviderTransport(Protocol):
    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        ...


@dataclass(frozen=True)
class FixtureTransport:
    response: ProviderSearchResponseModel

    @property
    def capabilities(self) -> ProviderCapabilities:
        return _capabilities(self.response)

    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        if self.response.research_id != request.research_id:
            raise ProviderContractError("provider research_id does not match request")
        return _response_to_result(self.response)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise ProviderUnavailable("provider redirect rejected")


class HttpMirrorTransport:
    def __init__(self, base_url: str | None = None, *, timeout: float = 10.0, max_bytes: int = 2_000_000, auth_token: str | None = None):
        self.base_url = (base_url or os.environ.get("NORA_COURTLISTENER_MIRROR_URL", "")).rstrip("/")
        self.timeout = max(0.1, min(timeout, 60.0))
        self.max_bytes = max(1024, min(max_bytes, 10_000_000))
        self.auth_token = auth_token or os.environ.get("NORA_COURTLISTENER_MIRROR_TOKEN")
        if not self.base_url.startswith("https://"):
            raise ProviderContractError("mirror URL must use HTTPS")

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(search=True)

    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        payload = ProviderSearchRequestModel(
            research_id=request.research_id,
            jurisdiction=request.jurisdiction,
            court_level=request.court_level,
            doctrinal_issue=request.doctrinal_issue,
            target_proposition=request.target_proposition,
            query_variants=list(request.query_variants),
            date_range=request.date_range,
            requested_capabilities=["search"],
        ).model_dump(mode="json")
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(self.base_url + "/v1/authority/search", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if self.auth_token:
            req.add_header("Authorization", "Bearer " + self.auth_token)
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                context = ssl.create_default_context()
                opener = urllib.request.build_opener(_NoRedirectHandler(), urllib.request.HTTPSHandler(context=context))
                with opener.open(req, timeout=self.timeout) as response:
                    raw = response.read(self.max_bytes + 1)
                    if len(raw) > self.max_bytes:
                        raise ProviderContractError("provider response exceeds size limit")
                    return _response_to_result(_parse_response(raw, request))
            except urllib.error.HTTPError as exc:
                if exc.code in {401, 403}:
                    raise ProviderAuthenticationError("provider authentication failed") from exc
                if exc.code == 429:
                    raise ProviderRateLimited("provider rate limit reached") from exc
                if exc.code in {400, 404, 409}:
                    raise ProviderContractError(f"provider rejected request with HTTP {exc.code}") from exc
                if exc.code < 500:
                    raise ProviderContractError(f"provider request failed with HTTP {exc.code}") from exc
                last_error = exc
            except (urllib.error.URLError, TimeoutError, ProviderUnavailable) as exc:
                last_error = exc
            if attempt == 0:
                time.sleep(0.05)
        raise ProviderUnavailable("provider service unavailable") from last_error


def _parse_response(raw: bytes, request: AuthorityResearchRequest) -> ProviderSearchResponseModel:
    try:
        response = ProviderSearchResponseModel.model_validate_json(raw)
    except Exception as exc:
        raise ProviderContractError("provider response schema invalid") from exc
    if response.provider_contract_version != 1 or response.research_id != request.research_id:
        raise ProviderContractError("provider response version or research_id mismatch")
    if response.partial:
        response.limitations.append("Provider reported a partial or truncated result.")
    return response


def _response_to_result(response: ProviderSearchResponseModel) -> ProviderSearchResult:
    capabilities = _capabilities(response)
    return ProviderSearchResult(
        provider=response.provider_name,
        capabilities=capabilities,
        authorities=tuple(item.model_dump(mode="json") for item in response.authorities),
        provenance={
            **response.provenance,
            "snapshot_id": response.snapshot_id,
            "snapshot_date": response.snapshot_date,
            "service_version": response.service_version,
        },
        limitations=tuple(response.limitations),
    )


def _capabilities(response: ProviderSearchResponseModel) -> ProviderCapabilities:
    return ProviderCapabilities(
        search=response.capabilities.get("search", False),
        opinion_retrieval=response.capabilities.get("opinion_retrieval", False),
        cluster_retrieval=response.capabilities.get("cluster_retrieval", False),
        court_metadata=response.capabilities.get("court_metadata", False),
        citation_graph_outbound=response.capabilities.get("citation_graph_outbound", False),
        citation_graph_inbound=response.capabilities.get("citation_graph_inbound", False),
        unsupported=tuple(k for k, value in response.capabilities.items() if value is False),
    )
