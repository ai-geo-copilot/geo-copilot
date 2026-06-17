from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlparse

from .errors import DnsResolutionError, UnsafeUrlError

Resolver = Callable[[str], list[str]]

_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain"}
_BLOCKED_IPS = {ipaddress.ip_address("169.254.169.254")}


def _default_resolver(hostname: str) -> list[str]:
    results = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    addresses: set[str] = set()
    for result in results:
        sockaddr = result[4]
        addresses.add(sockaddr[0])
    return sorted(addresses)


def _is_blocked_ip(address: ipaddress._BaseAddress) -> bool:
    return (
        address in _BLOCKED_IPS
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def validate_public_url(url: str, resolver: Resolver | None = None) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL hostname is required.")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in _BLOCKED_HOSTNAMES:
        raise UnsafeUrlError("Localhost URLs are not allowed.")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None

    if ip is not None:
        if _is_blocked_ip(ip):
            raise UnsafeUrlError("IP address is not allowed.")
        return url

    try:
        resolved_addresses = (resolver or _default_resolver)(hostname)
    except (OSError, socket.gaierror) as exc:
        raise DnsResolutionError("Hostname DNS resolution failed.") from exc
    if not resolved_addresses:
        raise DnsResolutionError("Hostname did not resolve to a public IP.")

    for resolved in resolved_addresses:
        try:
            address = ipaddress.ip_address(resolved)
        except ValueError as exc:
            raise DnsResolutionError("Resolver returned an invalid IP address.") from exc
        if _is_blocked_ip(address):
            raise UnsafeUrlError("Hostname resolved to a blocked IP.")
    return url
