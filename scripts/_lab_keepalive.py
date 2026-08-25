"""Keep local Next warm and print status (temp lab preview)."""
from __future__ import annotations

import time
import urllib.error
import urllib.request

URLS = [
    "http://127.0.0.1:3088/en/draft-preview",
    "http://127.0.0.1:3088/api/draft-preview/list",
]


def ping(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return f"{r.status}"
    except Exception as e:  # noqa: BLE001
        return f"ERR:{type(e).__name__}"


def main() -> None:
    while True:
        parts = [f"{u.split('/')[-1] or 'index'}={ping(u)}" for u in URLS]
        print(time.strftime("%H:%M:%S"), " ".join(parts), flush=True)
        time.sleep(45)


if __name__ == "__main__":
    main()
