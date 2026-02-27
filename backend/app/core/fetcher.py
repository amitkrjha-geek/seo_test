"""
Page fetcher module — async wrapper around the scripts/fetch_page.py logic.

Fetches a URL with proper headers, SSRF protection, redirect tracking,
and returns raw HTML plus response metadata for downstream analysis.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "SEO-Agency-Bot/1.0 (+https://github.com/AgriciDaniel/claude-seo)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class FetchError(Exception):
    """Raised when a page fetch fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _validate_url(url: str) -> str:
    """
    Validate and normalise a URL.

    * Prepends https:// when no scheme is present.
    * Rejects non-HTTP(S) schemes.
    * Blocks URLs that resolve to private / loopback / reserved IPs (SSRF
      prevention, mirrors logic from scripts/fetch_page.py).

    Returns the (possibly normalised) URL string.
    """
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise FetchError(f"Invalid URL scheme: {parsed.scheme}")

    if not parsed.hostname:
        raise FetchError("URL has no hostname")

    # SSRF guard — block private/internal IPs
    try:
        resolved_ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
            raise FetchError(
                f"Blocked: URL resolves to private/internal IP ({resolved_ip})"
            )
    except socket.gaierror:
        # DNS resolution will fail again inside httpx; let it surface there.
        pass

    return url


async def fetch_page(
    url: str,
    timeout: int = 30,
    follow_redirects: bool = True,
    max_redirects: int = 5,
    headers: dict[str, str] | None = None,
) -> dict:
    """
    Fetch a URL asynchronously and return raw HTML plus metadata.

    Parameters
    ----------
    url:
        The page URL to fetch.
    timeout:
        Request timeout in seconds.
    follow_redirects:
        Whether the client should follow HTTP redirects.
    max_redirects:
        Maximum number of redirects to follow before giving up.
    headers:
        Optional extra headers to merge with the defaults.

    Returns
    -------
    dict with keys:
        url              – final URL after redirects
        status_code      – HTTP status code
        html             – response body as text
        headers          – dict of response headers
        content_length   – character length of the HTML body
        redirect_chain   – list of intermediate redirect URLs
        error            – error message string, or None on success
    """
    result: dict = {
        "url": url,
        "status_code": None,
        "html": "",
        "headers": {},
        "content_length": 0,
        "redirect_chain": [],
        "error": None,
    }

    # --- Validate / normalise ------------------------------------------------
    try:
        url = _validate_url(url)
        result["url"] = url
    except FetchError as exc:
        result["error"] = str(exc)
        logger.warning("URL validation failed for %s: %s", url, exc)
        return result

    # --- Build merged headers ------------------------------------------------
    merged_headers = {**DEFAULT_HEADERS}
    if headers:
        merged_headers.update(headers)

    # --- Fetch ---------------------------------------------------------------
    try:
        async with httpx.AsyncClient(
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            timeout=httpx.Timeout(timeout),
        ) as client:
            response = await client.get(url, headers=merged_headers)

            result["url"] = str(response.url)
            result["status_code"] = response.status_code
            result["html"] = response.text
            result["headers"] = dict(response.headers)
            result["content_length"] = len(response.text)

            # Track the redirect chain (mirrors scripts/fetch_page.py)
            if response.history:
                result["redirect_chain"] = [
                    str(r.url) for r in response.history
                ]

    except httpx.TimeoutException:
        msg = f"Request timed out after {timeout} seconds"
        result["error"] = msg
        logger.error(msg)
    except httpx.TooManyRedirects:
        msg = f"Too many redirects (max {max_redirects})"
        result["error"] = msg
        logger.error(msg)
    except httpx.ConnectError as exc:
        msg = f"Connection error: {exc}"
        result["error"] = msg
        logger.error(msg)
    except httpx.HTTPStatusError as exc:
        msg = f"HTTP error: {exc}"
        result["error"] = msg
        result["status_code"] = exc.response.status_code
        logger.error(msg)
    except httpx.HTTPError as exc:
        msg = f"Request failed: {exc}"
        result["error"] = msg
        logger.error(msg)

    return result
