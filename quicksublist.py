import json
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
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

def process_json_file(json_path):
    if not os.path.isfile(json_path):
        print(f"❌ File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    episodes = data["data"]["episodes_list"]
    title = data["data"].get("title", "Subtitles")
    safe_title = sanitize_filename(title)
    output_dir = os.path.join(os.getcwd(), safe_title)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📂 [{safe_title}] Subtitles will be saved in: {output_dir}")
    print(f"📺 Downloading {len(episodes)} subtitle(s)...")

    retry_queue = []

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(download_subtitle, ep, output_dir): ep for ep in episodes}
        for future in as_completed(futures):
            ep, result = future.result()
            print(f"Episode {ep.get('name')}: {result}")
            if "Failed" in result:
                retry_queue.append(ep)

    if retry_queue:
        print(f"\n🔁 Retrying failed downloads ({len(retry_queue)}):")
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = {executor.submit(download_subtitle, ep, output_dir): ep for ep in retry_queue}
            for future in as_completed(futures):
                ep, result = future.result()
                print(f"Retry Episode {ep.get('name')}: {result}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python quicksub.py <json_file_or_list.txt>")
        return

    input_arg = sys.argv[1]

    if input_arg.lower().endswith(".txt"):
        with open(input_arg, "r", encoding="latin-1") as f:
            files = [line.strip().strip('"') for line in f if line.strip()]
        for json_file in files:
            process_json_file(json_file)
    else:
        process_json_file(input_arg)

    print("\n✅ All done.")

if __name__ == "__main__":
    main()
