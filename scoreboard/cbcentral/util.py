"""Central server access utilities."""

from scoreboard.cbcentral.api import central_api_get, central_api_post


def id_from_url(url):
    """Get player id from URL."""
    return url.strip("/").split("/")[-1]
