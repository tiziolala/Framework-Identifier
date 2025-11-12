from urllib.parse import urlparse

import requests

HEAD_TIMEOUT = 6
GET_TIMEOUT = 8
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def safe_head(session, url_base):
    """Try HEAD, return (response, method_used). If HEAD fails or returns 405, do GET."""
    try:
        r = session.head(url_base, allow_redirects=True, timeout=HEAD_TIMEOUT)
        # Some servers treat HEAD badly and return 405/501/403 — treat as "not allowed" and fallback
        if r.status_code in (405, 501):
            raise requests.RequestException("HEAD not supported; fallback")
        return r, "HEAD"
    except requests.RequestException:
        # fallback to GET (safe, non-intrusive)
        r = session.get(url_base, allow_redirects=True, timeout=GET_TIMEOUT)
        return r, "GET"

def add_scheme(url_base):
    url_base = url_base.strip()
    parsed = urlparse(url_base if "://" in url_base else f"//{url_base}", scheme="")
    netloc = parsed.netloc or parsed.path

    https = f"https://{netloc}/"
    http = f"http://{netloc}/"

    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.head(https, headers=headers, timeout=HEAD_TIMEOUT, allow_redirects=True)
        if r.status_code:
            return https
    except requests.RequestException:
        pass

    # fallback:
    return http