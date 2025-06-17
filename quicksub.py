import json
import os
import sys
import requests
import threading
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

MAX_RETRIES = 3
THREADS = 10
BASE_URL = "https://www.quicktv.vip"

def sanitize_filename(name):
    return re.sub(r'[\\\\/:*?"<>|]', '', name)

def download_subtitle(ep, output_dir, attempt=1):
    ep_name = ep.get("name")
    track_url = ep.get("track")

    if not ep_name or not track_url:
        return (ep, f"⚠️ Skipped (missing data)")

    full_url = urljoin(BASE_URL, track_url) if not track_url.startswith("http") else track_url
    file_path = os.path.join(output_dir, f"{ep_name}.vtt")

    try:
        response = requests.get(full_url, timeout=15)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        return (ep, "✅ Success")
    except Exception as e:
        if attempt < MAX_RETRIES:
            return download_subtitle(ep, output_dir, attempt + 1)
        return (ep, f"❌ Failed after {MAX_RETRIES} attempts: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python download_subtitles.py <json_file>")
        return

    json_file = sys.argv[1]
    if not os.path.isfile(json_file):
        print(f"❌ File not found: {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    episodes = data["data"]["episodes_list"]
    title = data["data"].get("title", "Subtitles")
    safe_title = sanitize_filename(title)
    output_dir = os.path.join(os.getcwd(), safe_title)
    os.makedirs(output_dir, exist_ok=True)

    print(f"📁 Subtitles will be saved in: {output_dir}")
    print(f"📺 Downloading {len(episodes)} subtitle(s)...")

    results = []
    retry_queue = []

    # Download using threads
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(download_subtitle, ep, output_dir): ep for ep in episodes}
        for future in as_completed(futures):
            ep, result = future.result()
            print(f"Episode {ep.get('name')}: {result}")
            if "Failed" in result:
                retry_queue.append(ep)

    # Retry failures (again threaded)
    if retry_queue:
        print(f"\n🔁 Retrying failed downloads ({len(retry_queue)}):")
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(download_subtitle, ep, output_dir): ep for ep in retry_queue}
            for future in as_completed(futures):
                ep, result = future.result()
                print(f"Retry Episode {ep.get('name')}: {result}")

    print("\n✅ Done.")

if __name__ == "__main__":
    main()
