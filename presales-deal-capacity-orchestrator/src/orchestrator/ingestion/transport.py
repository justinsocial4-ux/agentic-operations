from __future__ import annotations

import ipaddress
import re
import socket
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from urllib.parse import unquote, urlsplit

import httpx


class TransportDenied(ValueError):
    pass


class RedirectDenied(TransportDenied):
    pass


class TransportRequestError(RuntimeError):
    """Redacted transport failure. It never embeds a request, URL, header, or token."""


_DENIED_CALLER_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "host",
        "forwarded",
        "x-forwarded-for",
        "x-forwarded-host",
        "x-api-key",
    }
)
_RETRYABLE_STATUS = frozenset({408, 429, 502, 503, 504})


@dataclass(frozen=True)
class AllowedEndpoint:
    operation_id: str
    method: str
    host: str
    path_template: str
    idempotent_retryable: bool = False

    def matches(self, *, operation_id: str, method: str, host: str, path: str) -> bool:
        template_pattern = re.escape(self.path_template)
        template_pattern = re.sub(r"\\\{[^{}]+\\\}", r"[^/]+", template_pattern)
        return (
            operation_id == self.operation_id
            and method == self.method
            and host == self.host
            and re.fullmatch(template_pattern, path) is not None
        )


class EphemeralCredential:
    """A process-memory-only header issued by an adapter from direct user input."""

    __slots__ = ("__header_name", "__header_value")

    def __init__(self, *, header_name: str, header_value: str) -> None:
        if header_name.lower() not in {"authorization", "x-api-key"}:
            raise ValueError("credential header is not supported")
        if not header_value or "\r" in header_value or "\n" in header_value:
            raise ValueError("invalid session credential")
        self.__header_name = header_name
        self.__header_value = header_value

    @classmethod
    def bearer(cls, token: str) -> "EphemeralCredential":
        return cls(header_name="Authorization", header_value=f"Bearer {token}")

    @classmethod
    def authorization_value(cls, token: str) -> "EphemeralCredential":
        return cls(header_name="Authorization", header_value=token)

    def _issued_header(self) -> tuple[str, str]:
        return self.__header_name, self.__header_value

    def __repr__(self) -> str:
        return "EphemeralCredential(<redacted>)"

    def __reduce__(self) -> object:
        raise TypeError("session credentials cannot be serialized")


@dataclass(frozen=True)
class RetryAttemptV1:
    attempt: int
    reason: str
    bounded_delay_seconds: float


def _validate_common_url(url: str) -> tuple[str, str, int | None, str]:
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise TransportDenied("URL userinfo is forbidden")
    if parsed.fragment:
        raise TransportDenied("URL fragments are forbidden")
    if not parsed.hostname:
        raise TransportDenied("URL requires a hostname")
    if "%" in parsed.netloc or unquote(parsed.netloc) != parsed.netloc:
        raise TransportDenied("encoded authority is forbidden")
    try:
        port = parsed.port
    except ValueError as exc:
        raise TransportDenied("invalid port") from exc
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    return parsed.scheme.lower(), host, port, parsed.path or "/"


def validate_vendor_url(url: str, *, approved_hosts: frozenset[str]) -> tuple[str, str]:
    scheme, host, port, path = _validate_common_url(url)
    if scheme != "https":
        raise TransportDenied("vendor endpoint requires HTTPS")
    if port not in (None, 443):
        raise TransportDenied("alternate vendor ports are forbidden")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise TransportDenied("vendor IP literals are forbidden")
    if host not in approved_hosts:
        raise TransportDenied("vendor host is not exactly allowlisted")
    return host, path


def validate_public_dns_evidence(
    first_resolution: Sequence[str], second_resolution: Sequence[str] | None = None,
) -> tuple[str, ...]:
    """Validate resolver evidence supplied by authorized preflight, without doing hidden DNS in tests."""
    if not first_resolution:
        raise TransportDenied("vendor DNS resolution produced no addresses")
    first = tuple(sorted(set(first_resolution)))
    for raw in first:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise TransportDenied("invalid DNS address evidence") from exc
        if not address.is_global or address.is_multicast or address.is_link_local:
            raise TransportDenied("vendor DNS resolved to a non-public address")
    if second_resolution is not None and first != tuple(sorted(set(second_resolution))):
        raise TransportDenied("DNS rebinding evidence detected")
    return first


def validate_loopback_url(url: str) -> tuple[str, int | None, str]:
    scheme, host, port, path = _validate_common_url(url)
    if scheme not in {"http", "https"}:
        raise TransportDenied("local model scheme must be HTTP or HTTPS")
    if host == "localhost":
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, port or 80, type=socket.SOCK_STREAM)
        }
        if not addresses or any(not ipaddress.ip_address(address).is_loopback for address in addresses):
            raise TransportDenied("localhost resolved outside loopback")
    else:
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise TransportDenied("local model host must be a loopback literal or localhost") from exc
        if getattr(address, "ipv4_mapped", None) is not None:
            raise TransportDenied("IPv4-mapped loopback addresses are forbidden")
        if not address.is_loopback:
            raise TransportDenied("non-loopback local model endpoint denied")
    return host, port, path


def validate_caller_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    clean = dict(headers or {})
    denied = sorted(key for key in clean if key.lower() in _DENIED_CALLER_HEADERS)
    if denied:
        raise TransportDenied(f"caller-controlled ambient/auth headers denied: {', '.join(denied)}")
    return clean


def build_httpx_client(*, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """The only HTTPX factory: environment trust, redirects, and TLS bypass are not parameters."""
    return httpx.Client(
        trust_env=False,
        follow_redirects=False,
        verify=True,
        timeout=httpx.Timeout(20.0, connect=10.0),
        transport=transport,
    )


def _bounded_retry_after(value: str | None, *, now: Callable[[], float]) -> float | None:
    if value is None:
        return None
    try:
        delay = float(value)
    except ValueError:
        try:
            delay = parsedate_to_datetime(value).timestamp() - now()
        except (TypeError, ValueError, OverflowError):
            return None
    return delay if 0 <= delay <= 8 else None


class LockedHttpClient:
    def __init__(
        self,
        endpoints: tuple[AllowedEndpoint, ...],
        *,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._endpoints = endpoints
        self._client = client or build_httpx_client()
        self._sleeper = sleeper
        self._now = now
        self.last_retry_trace: tuple[RetryAttemptV1, ...] = ()
        ambient = {key.lower() for key in self._client.headers}
        if ambient & _DENIED_CALLER_HEADERS:
            raise TransportDenied("HTTP client contains an ambient authentication header")
        if getattr(self._client, "_auth", None) is not None:
            raise TransportDenied("HTTP client contains ambient authentication")

    def close(self) -> None:
        self._client.close()

    def _approved_endpoint(self, *, operation_id: str, method: str, host: str, path: str) -> AllowedEndpoint:
        for endpoint in self._endpoints:
            if endpoint.matches(operation_id=operation_id, method=method, host=host, path=path):
                return endpoint
        raise TransportDenied("operation/method/host/path tuple is not allowlisted")

    def request(
        self,
        *,
        operation_id: str,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        credential: EphemeralCredential | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        normalized_method = method.upper()
        approved_hosts = frozenset(endpoint.host for endpoint in self._endpoints)
        host, path = validate_vendor_url(url, approved_hosts=approved_hosts)
        self._approved_endpoint(operation_id=operation_id, method=normalized_method, host=host, path=path)
        if normalized_method == "GET" and content is not None:
            raise TransportDenied("GET request bodies are forbidden")
        clean_headers = validate_caller_headers(headers)
        if credential is not None:
            name, value = credential._issued_header()
            clean_headers[name] = value
        self._client.cookies.clear()
        try:
            response = self._client.request(
                normalized_method,
                url,
                headers=clean_headers,
                content=content,
                follow_redirects=False,
            )
            if 300 <= response.status_code < 400:
                raise RedirectDenied("redirect response denied")
            return response
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError):
            raise TransportRequestError("vendor request failed") from None
        finally:
            self._client.cookies.clear()

    def request_with_retry(self, **kwargs: object) -> httpx.Response:
        method = str(kwargs["method"]).upper()
        url = str(kwargs["url"])
        host, path = validate_vendor_url(url, approved_hosts=frozenset(e.host for e in self._endpoints))
        endpoint = self._approved_endpoint(
            operation_id=str(kwargs["operation_id"]), method=method, host=host, path=path,
        )
        if not endpoint.idempotent_retryable:
            return self.request(**kwargs)  # type: ignore[arg-type]
        trace: list[RetryAttemptV1] = []
        for attempt in range(1, 5):
            try:
                response = self.request(**kwargs)  # type: ignore[arg-type]
                if response.status_code not in _RETRYABLE_STATUS or attempt == 4:
                    self.last_retry_trace = tuple(trace)
                    return response
                reason = f"HTTP_{response.status_code}"
                delay = _bounded_retry_after(response.headers.get("retry-after"), now=self._now)
            except TransportRequestError:
                if attempt == 4:
                    self.last_retry_trace = tuple(trace)
                    raise
                reason = "NETWORK_OR_TIMEOUT"
                delay = None
            if delay is None:
                delay = float(min(2 ** (attempt - 1), 8))
            trace.append(RetryAttemptV1(attempt=attempt, reason=reason, bounded_delay_seconds=delay))
            self._sleeper(delay)
        raise AssertionError("bounded retry loop exhausted unexpectedly")
