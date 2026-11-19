import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

USER_AGENT = "book-price-tracker/1.0"
RETRYABLE_STATUSES = [429, 500, 502, 503, 504]


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    adapter = HTTPAdapter(
        max_retries=Retry(total=3, backoff_factor=1, status_forcelist=RETRYABLE_STATUSES)
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_html(session: requests.Session, url: str, timeout: float) -> bytes | None:
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as error:
        logger.warning("Failed to fetch %s: %s", url, error)
        return None
    return response.content
