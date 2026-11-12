#!/usr/bin/env python3
"""Create a website photo manifest from files in sample-photos/.

Upload photos directly in GitHub. This action automatically refreshes photos.json.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "sample-photos"
MANIFEST = PHOTO_DIR / "photos.json"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def main():
    # Use stable alphabetical ordering; names beginning with 01, 02, etc. control order.
    images = sorted(
        (file for file in PHOTO_DIR.iterdir()
         if file.is_file() and file.suffix.lower() in EXTENSIONS),
        key=lambda file: file.name.casefold(),
    )
    # Keep all photos in manifest. Frontend displays the first ten.
    photos = [f"sample-photos/{file.name}" for file in images]
    new_text = json.dumps({"photos": photos}, ensure_ascii=False, indent=2) + "\n"
    if MANIFEST.exists() and MANIFEST.read_text(encoding="utf-8") == new_text:
        print("Photo list unchanged.")
        return
    MANIFEST.write_text(new_text, encoding="utf-8")
    print(f"Indexed {len(photos)} sample photos.")

if __name__ == "__main__":
    main()
