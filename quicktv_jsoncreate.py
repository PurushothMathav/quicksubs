import json
import csv
import os
import re
import requests
from urllib.parse import urljoin

# CONFIG
API_TEMPLATE = "https://www.quicktv.vip/addons/dramas/video/detail?id={show_id}"
INPUT_CSV = "category_ids.csv"
OUTPUT_DIR = "json"
LOG_FILE = "quicktv_log.txt"
TRACK_DOMAIN = "https://www.quicktv.vip"

# Setup
os.makedirs(OUTPUT_DIR, exist_ok=True)
log_entries = []

def log(msg):
    print(msg)
    log_entries.append(msg)

def fetch_show(show_id):
    url = API_TEMPLATE.format(show_id=show_id)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()

def clean_escape_slashes(episodes):
    for ep in episodes:
        if ep.get("url"):
            ep["url"] = ep["url"].replace("\\", "")
        if ep.get("track"):
            ep["track"] = ep["track"].replace("\\", "")
    return episodes

def fix_urls(data):
    episodes = data["data"]["episodes_list"]
    episodes = clean_escape_slashes(episodes)
    base_url = None
    ext = "mp4"

    for ep in episodes:
        url = ep.get("url", "")
        match = re.match(r"(.*/)(0?1)\.(mp4|mov|mkv)$", url)
        if match:
            base_url = match.group(1)
            ext = match.group(3)
            break

    if not base_url:
        return None

    for ep in episodes:
        name = ep.get("name").zfill(2)  # Normalize: 1 → 01
        if not ep.get("url"):
            ep["url"] = f"{base_url}{name}.{ext}"
        if ep.get("track", "").startswith("/"):
            ep["track"] = urljoin(TRACK_DOMAIN, ep["track"])

    return data

def is_valid_episode1_url(url):
    if not url:
        return False
    clean_url = url.replace('\\', '').split("?")[0]
    return re.search(r"/0?1\.(mp4|mov|mkv)$", clean_url) is not None

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row["title"].strip()
            show_id = row["id"].strip()

            try:
                log(f"🔍 Processing: {title} (ID: {show_id})")
                data = fetch_show(show_id)
                episodes = data["data"].get("episodes_list", [])
                episodes = clean_escape_slashes(episodes)

                if not episodes or not isinstance(episodes[0], dict):
                    log(f"❌ Skipped (no valid episodes)")
                    continue

                ep1_url = episodes[0].get("url")
                if is_valid_episode1_url(ep1_url):
                    updated = fix_urls(data)
                    if not updated:
                        log(f"❌ Skipped (couldn't determine base URL): {title}")
                        continue

                    safe_title = re.sub(r'[\\\\/:*?"<>|]', '', title)
                    out_path = os.path.join(OUTPUT_DIR, f"{safe_title}.json")
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(updated, f, ensure_ascii=False, indent=2)
                    log(f"✅ Saved: {safe_title}.json")
                else:
                    log(f"❌ Skipped (Episode 1 URL not valid: {ep1_url})")

            except Exception as e:
                log(f"❌ Error with {title} (ID: {show_id}): {e}")

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_entries))
    print(f"\n📄 Log saved to {LOG_FILE}")

if __name__ == "__main__":
    main()
