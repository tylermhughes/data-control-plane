"""Which webhook URLs DCP will send to.

http and https are both allowed (self-hosted tools often use plain http on an internal
network). Cloud metadata addresses are always blocked, both when the URL is saved and when
it is resolved at send time, because they can hand out the server's cloud credentials.
"""

import ipaddress
import socket
from urllib.parse import urlsplit

BLOCKED_NETWORKS = (
    ipaddress.ip_network("169.254.0.0/16"),  # link-local, incl. AWS/GCP/Azure metadata
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
    ipaddress.ip_network("fd00:ec2::254/128"),  # AWS IPv6 metadata
)
BLOCKED_HOSTS = frozenset({"metadata.google.internal", "metadata"})


def _blocked(ip: str) -> bool:
    address = ipaddress.ip_address(ip.split("%", 1)[0])
    return any(address in network for network in BLOCKED_NETWORKS)


def check_webhook_url(url: str) -> None:
    """Raises ValueError with a plain-language reason if the URL isn't allowed."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError("webhook URLs must start with http:// or https://")
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("webhook URL has no host")
    if host in BLOCKED_HOSTS:
        raise ValueError("cloud metadata addresses can't receive webhooks")
    try:
        is_blocked_ip = _blocked(host)
    except ValueError:
        return  # a hostname, not an IP: checked again when it's resolved at send time
    if is_blocked_ip:
        raise ValueError("link-local and cloud metadata addresses can't receive webhooks")


def check_resolved(url: str) -> None:
    """At send time: refuse if the host resolves to a blocked address."""
    parts = urlsplit(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    for info in socket.getaddrinfo(parts.hostname or "", port, proto=socket.IPPROTO_TCP):
        if _blocked(str(info[4][0])):
            raise ValueError(f"{parts.hostname} resolves to a blocked address")
