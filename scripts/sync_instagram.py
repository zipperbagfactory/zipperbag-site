#!/usr/bin/env python3
"""Sync an authorized Instagram Business account's latest sample photos.

This script runs on GitHub Actions, never in a visitor's browser. The access
token must live only in the INSTAGRAM_ACCESS_TOKEN GitHub Actions secret.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

OUTPUT = Path(__file__).resolve().parents[1] / "instagram-posts.json"
API_ROOT = "https://graph.instagram.com/v26.0"
PHOTO_LIMIT = 5


def get_json(url: str, token: str) -> dict:
    if not url.startswith(API_ROOT + "/"):
        raise ValueError("Unexpected Instagram API URL.")
    req = Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "User-Agent": "ZipperbagWebsitePhotoSync/1.0",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read(3_000_000))
    except HTTPError as exc:
        # Intentionally never print the request headers, response body, or token.
        raise RuntimeError(
            f"Instagram API returned HTTP {exc.code}; verify permission and token validity."
        ) from None
    except URLError as exc:
        raise RuntimeError("Instagram API could not be reached. Existing data is kept.") from None


def safe_public_post(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and parsed.hostname in {
            "instagram.com", "www.instagram.com"
        }
    except ValueError:
        return False


def safe_image(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme == "https" and bool(p.netloc)
    except ValueError:
        return False


def first_carousel_photo(media_id: str, token: str) -> str:
    # A carousel post may not expose its cover through media_url.
    # Look at its first accessible image child.
    if not media_id.isdigit():
        return ""
    params = urlencode({"fields": "id,media_type,media_url", "limit": 10})
    try:
        response = get_json(f"{API_ROOT}/{media_id}/children?{params}", token)
    except RuntimeError:
        return ""
    for child in response.get("data", []):
        if child.get("media_type") == "IMAGE" and safe_image(child.get("media_url", "")):
            return child["media_url"]
    return ""


def sync(token: str) -> None:
    # Scope: instagram_business_basic. Read-only; no publishing permission needed.
    fields = "id,media_type,media_url,permalink,timestamp"
    params = urlencode({"fields": fields, "limit": 50})
    result = get_json(f"{API_ROOT}/me/media?{params}", token)
    media = result.get("data", [])
    if not isinstance(media, list):
        raise RuntimeError("Instagram returned an unexpected media response.")

    result_photos = []
    seen = set()
    for post in sorted(media, key=lambda p: p.get("timestamp", ""), reverse=True):
        permalink = str(post.get("permalink") or "")
        post_id = str(post.get("id") or "")
        if not safe_public_post(permalink) or post_id in seen:
            continue
        media_type = post.get("media_type")
        if media_type == "IMAGE":
            image = str(post.get("media_url") or "")
        elif media_type == "CAROUSEL_ALBUM":
            image = str(post.get("media_url") or "")
            if not safe_image(image):
                image = first_carousel_photo(post_id, token)
        else:
            # No video or Reel in the sample photo slider.
            continue
        if not safe_image(image):
            continue
        seen.add(post_id)
        result_photos.append({
            "id": post_id,
            "url": permalink,
            "image": image,
            "date": str(post.get("timestamp") or "")[:10],
        })
        if len(result_photos) >= PHOTO_LIMIT:
            break

    if not result_photos:
        raise RuntimeError(
            "No eligible public IMAGE posts were found. Previous data is preserved."
        )

    new_data = {"posts": result_photos}
    previous = None
    if OUTPUT.exists():
        try:
            previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass

    if previous == new_data:
        print("Instagram photo list unchanged.")
        return
    OUTPUT.write_text(
        json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(result_photos)} Instagram sample photos.")


if __name__ == "__main__":
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not access_token:
        print("::notice::Set the INSTAGRAM_ACCESS_TOKEN Actions secret to enable Instagram syncing.")
    else:
        sync(access_token)
