#!/usr/bin/env python3
"""Generate sitemap.xml from published HTML files in this GitHub Pages repository."""
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.zipperbag.net"
EXCLUDE = {"404.html"}
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
urlset = ET.Element(namespace + "urlset")
pages = sorted(
    (p for p in ROOT.rglob("*.html")
     if ".git" not in p.parts and ".github" not in p.parts
     and not any(part.startswith("_") for part in p.relative_to(ROOT).parts)
     and p.name not in EXCLUDE),
    key=lambda p: (p.relative_to(ROOT).as_posix() != "index.html", p.relative_to(ROOT).as_posix())
)
for page in pages:
    relative = page.relative_to(ROOT).as_posix()
    url = BASE + ("/" if relative == "index.html" else "/" + quote(relative, safe="/-._~"))
    entry = ET.SubElement(urlset, namespace + "url")
    ET.SubElement(entry, namespace + "loc").text = url
ET.indent(urlset, space="  ")
output = ROOT / "sitemap.xml"
output.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="utf-8"))
print(f"Generated sitemap with {len(pages)} URLs")
