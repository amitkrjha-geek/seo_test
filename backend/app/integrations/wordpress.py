"""
WordPress REST API client for publishing content.
Uses the WP REST API v2 with Application Passwords (Basic Auth).
Docs: https://developer.wordpress.org/rest-api/
"""

import base64
import httpx

DEFAULT_TIMEOUT = 30.0


def _auth_header(username: str, app_password: str) -> dict[str, str]:
    """Build HTTP Basic auth header for WordPress Application Passwords."""
    credentials = f"{username}:{app_password}"
    token = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


async def test_connection(
    site_url: str,
    username: str,
    app_password: str,
) -> dict:
    """
    Test a WordPress connection by fetching the authenticated user profile.

    Args:
        site_url: WordPress site URL (e.g. https://example.com).
        username: WordPress username.
        app_password: WordPress Application Password.

    Returns:
        dict with success (bool) and message (str).
    """
    url = f"{site_url.rstrip('/')}/wp-json/wp/v2/users/me"
    headers = _auth_header(username, app_password)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            display_name = data.get("name", username)
            return {
                "success": True,
                "message": f"Connected as {display_name}",
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {
                "success": False,
                "message": "Authentication failed. Check your username and application password.",
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


async def publish_post(
    site_url: str,
    username: str,
    app_password: str,
    title: str,
    content_html: str,
    status: str = "publish",
) -> dict:
    """
    Create a new post on WordPress.

    Args:
        site_url: WordPress site URL.
        username: WordPress username.
        app_password: WordPress Application Password.
        title: Post title.
        content_html: Post content as HTML.
        status: Post status - "publish", "draft", or "pending".

    Returns:
        dict with external_id, external_url on success, or error on failure.
    """
    url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    headers = _auth_header(username, app_password)
    payload = {
        "title": title,
        "content": content_html,
        "status": status,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return {
                "external_id": str(data.get("id", "")),
                "external_url": data.get("link", ""),
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


async def list_categories(
    site_url: str,
    username: str,
    app_password: str,
) -> dict:
    """
    List available categories on the WordPress site.

    Args:
        site_url: WordPress site URL.
        username: WordPress username.
        app_password: WordPress Application Password.

    Returns:
        dict with categories list on success, or error on failure.
    """
    url = f"{site_url.rstrip('/')}/wp-json/wp/v2/categories"
    headers = _auth_header(username, app_password)

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=headers, params={"per_page": 100})
            response.raise_for_status()
            data = response.json()
            return {
                "categories": [
                    {
                        "id": cat.get("id"),
                        "name": cat.get("name"),
                        "slug": cat.get("slug"),
                        "count": cat.get("count", 0),
                    }
                    for cat in data
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
