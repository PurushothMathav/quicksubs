import json
import os
import re
import requests
from urllib.parse import urljoin

TRACK_DOMAIN = "https://www.quicktv.vip"
VIDEO_DOMAIN = "https://liketv.oss-cn-hongkong.aliyuncs.com/0yuanbao"

def fetch_show(show_id):
    url = f"https://www.quicktv.vip/addons/dramas/video/detail?id={show_id}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()

def guess_base_url(show_data):
    title = show_data["data"].get("title", "unknown")
    clean_title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', title)
    base_url = f"{VIDEO_DOMAIN}/{clean_title}/"
    print(f"⚠️ Using fallback video base URL: {base_url}")
    return base_url

def fix_urls(data):
    episodes = data["data"]["episodes_list"]

    # Try to get base URL and extension from any full video URL
    base_url = None
    extension = "mp4"  # default fallback

    for ep in episodes:
        url = ep.get("url")
        if isinstance(url, str):
            match = re.match(r"(.*/)(\d+)\.(\w+)$", url)
            if match:
                base_url = match.group(1)
                extension = match.group(3)
                break

    if not base_url:
        base_url = guess_base_url(data)
        print(f"⚠️ Falling back to base URL: {base_url}")

    print(f"📺 Video base: {base_url}, extension: .{extension}")

    for ep in episodes:
        name = ep.get("name")
        if not ep.get("url"):
            ep["url"] = f"{base_url}{name}.{extension}"

        track = ep.get("track", "")
        if track.startswith("/"):
            ep["track"] = urljoin(TRACK_DOMAIN, track)

    return data

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python quicktv_json.py <show_id>")
        return

    show_id = sys.argv[1]
    print(f"🔍 Fetching show ID: {show_id}")
    data = fetch_show(show_id)
    updated = fix_urls(data)

    title = updated["data"].get("title", f"show_{show_id}")
    safe_title = re.sub(r'[\\\\/:*?\"<>|]', '', title)
    out_file = f"{safe_title}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved updated JSON: {out_file}")

if __name__ == "__main__":
    main()
