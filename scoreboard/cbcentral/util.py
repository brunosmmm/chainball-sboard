"""Central server access utilities."""

import hashlib


def id_from_url(url):
    """Get player id from URL."""
    return url.strip("/").split("/")[-1]


def md5_sum(file_name):
    """Calculate MD5 sum."""
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as data:
        for chunk in iter(lambda: data.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()
