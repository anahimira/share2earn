import requests
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor


def check_proxy_live(proxy_url: str, timeout: int = 5) -> str:
    try:
        if '://' not in proxy_url:
            proxy_url = 'http://' + proxy_url  # Default to http

        parsed = urlparse(proxy_url)
        scheme = parsed.scheme.lower()
        username = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        host = parsed.hostname
        port = parsed.port or (1080 if scheme.startswith('socks') else 80)

        # Build proxies dict
        if scheme.startswith('socks5'):
            proxy_auth = f"{username}:{password}@" if username and password else ""
            proxy_str = f"socks5h://{proxy_auth}{host}:{port}"
            proxies = {"http": proxy_str, "https": proxy_str}
        elif scheme in ['http', 'https']:
            proxies = {"http": proxy_url, "https": proxy_url}
        else:
            proxies = {"http": proxy_url, "https": proxy_url}

        # Send test request
        resp = requests.get('https://www.google.com/', proxies=proxies, timeout=timeout)
        return 'online' if resp.status_code == 200 else 'offline'
    except Exception:
        return 'offline'


def run_check_proxies(proxy_list, timeout=5):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda p: check_proxy_live(p, timeout), proxy_list))
    return results
