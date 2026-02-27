"""
Strapi REST API client for publishing content.
Supports Strapi v4+ with Bearer token authentication.
Docs: https://docs.strapi.io/dev-docs/api/rest
"""

import httpx

DEFAULT_TIMEOUT = 30.0


def _auth_headers(bearer_token: str) -> dict[str, str]:
    """Build Bearer auth headers for Strapi API."""
    return {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }


async def test_connection(
    site_url: str,
    bearer_token: str,
) -> dict:
    """
    Test a Strapi connection by fetching available content types.

    Args:
        site_url: Strapi instance URL (e.g. https://cms.example.com).
        bearer_token: Strapi API token (full access or custom).

    Returns:
        dict with success (bool) and message (str).
    """
    url = f"{site_url.rstrip('/')}/api/content-types"
    headers = _auth_headers(bearer_token)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Strapi v4 returns { data: [...] }
            content_types = data.get("data", [])
            count = len(content_types) if isinstance(content_types, list) else 0
            return {
                "success": True,
                "message": f"Connected successfully. {count} content types available.",
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {
                "success": False,
                "message": "Authentication failed. Check your API token.",
            }
        if exc.response.status_code == 403:
            return {
                "success": False,
                "message": "Access denied. Your token may not have sufficient permissions.",
            }
        return {
            "success": False,
            "message": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
        }
    except httpx.RequestError as exc:
        return {
            "success": False,
            "message": f"Connection failed: {str(exc)}",
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"Unexpected error: {str(exc)}",
        }


async def publish_entry(
    site_url: str,
    bearer_token: str,
    content_type: str,
    data: dict,
) -> dict:
    """
    Create a new entry in a Strapi collection type.

    Args:
        site_url: Strapi instance URL.
        bearer_token: Strapi API token.
        content_type: Strapi collection type plural name (e.g. "articles").
        data: The entry data fields to create.

    Returns:
        dict with external_id and external_url on success, or error on failure.
    """
    url = f"{site_url.rstrip('/')}/api/{content_type}"
    headers = _auth_headers(bearer_token)
    payload = {"data": data}

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Strapi v4 response: { data: { id, attributes: {...} } }
            entry_data = result.get("data", {})
            entry_id = entry_data.get("id", "")

            # Build an external URL pointing to the admin panel entry
            admin_url = f"{site_url.rstrip('/')}/admin/content-manager/collection-types/api::{content_type}.{content_type}/{entry_id}"

            return {
                "external_id": str(entry_id),
                "external_url": admin_url,
            }
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
        }
    except httpx.RequestError as exc:
        return {
            "error": f"Request failed: {str(exc)}",
        }
    except Exception as exc:
        return {
            "error": f"Unexpected error: {str(exc)}",
        }


async def list_content_types(
    site_url: str,
    bearer_token: str,
) -> dict:
    """
    List available collection types from Strapi.

    Args:
        site_url: Strapi instance URL.
        bearer_token: Strapi API token.

    Returns:
        dict with content_types list on success, or error on failure.
    """
    url = f"{site_url.rstrip('/')}/api/content-types"
    headers = _auth_headers(bearer_token)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            content_types = data.get("data", [])
            return {
                "content_types": [
                    {
                        "uid": ct.get("uid", ""),
                        "kind": ct.get("schema", {}).get("kind", ""),
                        "display_name": ct.get("schema", {}).get("displayName", ""),
                    }
                    for ct in content_types
                    if isinstance(ct, dict)
                ],
            }
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
        }
    except httpx.RequestError as exc:
        return {
            "error": f"Request failed: {str(exc)}",
        }
    except Exception as exc:
        return {
            "error": f"Unexpected error: {str(exc)}",
        }
