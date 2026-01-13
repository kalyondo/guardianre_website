#!/usr/bin/env python3
"""
WordPress Media Fetch Script
Downloads media files from original URLs if they are still accessible.
"""

import os
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

# Paths
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / 'content'
OUTPUT_DIR = BASE_DIR / 'public' / 'images' / 'uploads'

def load_media_manifest():
    """Load media manifest from content directory."""
    manifest_path = CONTENT_DIR / 'media-manifest.json'
    if not manifest_path.exists():
        print(f"[ERROR] Media manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to output path."""
    try:
        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MediaFetcher/1.0)'
        }
        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        return True

    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {url}")
        return False
    except urllib.error.URLError as e:
        print(f"  [URL Error] {url}: {e.reason}")
        return False
    except Exception as e:
        print(f"  [Error] {url}: {e}")
        return False

def main():
    """Main function to download all media."""
    print("=" * 60)
    print("WordPress Media Fetch")
    print("=" * 60)

    # Load manifest
    manifest = load_media_manifest()
    total = len(manifest)
    print(f"\n[INFO] Found {total} media items in manifest")

    # Statistics
    downloaded = 0
    skipped = 0
    failed = 0

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] Downloading to: {OUTPUT_DIR}")
    print("-" * 40)

    for i, item in enumerate(manifest, 1):
        url = item.get('url', '')
        file_path = item.get('file', '')

        if not url:
            skipped += 1
            continue

        # Determine output path
        if file_path:
            # Use the WordPress uploads path structure
            output_path = OUTPUT_DIR / file_path
        else:
            # Extract filename from URL
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename:
                skipped += 1
                continue
            output_path = OUTPUT_DIR / filename

        # Skip if already downloaded
        if output_path.exists():
            print(f"[{i}/{total}] Skipped (exists): {output_path.name}")
            skipped += 1
            continue

        # Download
        print(f"[{i}/{total}] Downloading: {item.get('title', 'Unknown')[:40]}...")

        if download_file(url, output_path):
            downloaded += 1
            print(f"  [OK] Saved: {output_path.name}")
        else:
            failed += 1

        # Rate limiting
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  Total items: {total}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"\n  Output directory: {OUTPUT_DIR}")

    if failed > 0:
        print(f"\n[WARNING] {failed} files could not be downloaded.")
        print("  This may be because the original site is no longer accessible.")
        print("  You can add placeholder images or source them from other locations.")

    print("\n[DONE] Media fetch complete!")

if __name__ == '__main__':
    main()
