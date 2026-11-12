#!/usr/bin/env python3
"""Sync recent public Naver blog RSS entries to a small website JSON file."""
from __future__ import annotations

import json
import re
from datetime import timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

FEED_URL = "https://rss.blog.naver.com/zipperbagnet.xml"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "blog-posts.json"
BLOG_HOSTS = {"blog.naver.com", "m.blog.naver.com"}
IMAGE_HOSTS = {
    "postfiles.pstatic.net", "blogfiles.pstatic.net",
    "blogthumb.pstatic.net", "mblogthumb-phinf.pstatic.net",
    "phinf.pstatic.net", "blogpfthumb-phinf.pstatic.net",
}


class SummaryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.image = ""
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style"}:
            self.skip_depth += 1
        elif tag == "img" and not self.image:
            src = attrs.get("src") or attrs.get("data-src") or ""
            if valid_image(src):
                self.image = src
        elif tag in {"br", "p", "div", "li"} and not self.skip_depth:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, text):
        if not self.skip_depth:
            self.parts.append(text)


def valid_image(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.scheme == "https" and (u.hostname or "").lower() in IMAGE_HOSTS
    except ValueError:
        return False


def text_of(node, name: str) -> str:
    return (node.findtext(name) or "").strip()


def extract_feed() -> list[dict]:
    request = Request(
        FEED_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ZipperbagBlogFeed/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urlopen(request, timeout=25) as response:
        xml = response.read(3_000_000)
    root = ElementTree.fromstring(xml)
    items = root.findall("./channel/item")
    if not items:
        raise RuntimeError("RSS has no visible posts; keeping the previous website data.")

    posts: list[dict] = []
    seen: set[str] = set()
    for item in items:
        title = re.sub(r"\s+", " ", unescape(text_of(item, "title"))).strip()
        url = text_of(item, "link")
        try:
            u = urlparse(url)
        except ValueError:
            continue
        if u.scheme not in {"https", "http"} or (u.hostname or "").lower() not in BLOG_HOSTS:
            continue
        if not title or url in seen:
            continue
        seen.add(url)

        raw_description = text_of(item, "description")
        parser = SummaryParser()
        parser.feed(raw_description)
        summary = re.sub(r"\s+", " ", unescape("".join(parser.parts))).strip()
        if len(summary) > 115:
            summary = summary[:115].rsplit(" ", 1)[0] + "…"

        pub_date = text_of(item, "pubDate")
        try:
            date = parsedate_to_datetime(pub_date).date().isoformat()
        except (TypeError, ValueError, IndexError):
            date = ""

        posts.append({
            "title": title[:160],
            "url": url,
            "date": date,
            "excerpt": summary,
            "image": parser.image,
        })
        if len(posts) == 3:
            break
    if not posts:
        raise RuntimeError("RSS returned no valid public blog post URLs.")
    return posts


def main():
    posts = extract_feed()
    payload = {"source": FEED_URL, "posts": posts}
    old = None
    if OUTPUT_PATH.exists():
        try:
            old = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    if old == payload:
        print("Blog posts unchanged.")
        return
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {len(posts)} blog posts.")


if __name__ == "__main__":
    main()
