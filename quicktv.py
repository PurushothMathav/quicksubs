import json
import sys
import os
import re

def extract_base_url(episodes):
    for ep in episodes:
        url = ep.get("url")
        if url:
            match = re.match(r"(.*/)(\d+)\.mp4$", url)
            if match:
                return match.group(1)
    return None

def fill_missing_data(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    episodes = data["data"]["episodes_list"]
    base_url_prefix = extract_base_url(episodes)

    if not base_url_prefix:
        print("❌ Could not determine base_url_prefix from existing URLs.")
        sys.exit(1)

    track_base_url = "https://www.quicktv.vip"

    for episode in episodes:
        # Fill missing video URLs
        if not episode.get("url"):
            try:
                ep_num = int(episode["name"])
                episode["url"] = f"{base_url_prefix}{ep_num}.mp4"
            except ValueError:
                print(f"⚠️  Warning: Could not parse episode number from name: {episode['name']}")

        # Fix incomplete 'track' URLs
        track = episode.get("track")
        if track and track.startswith("/"):
            episode["track"] = track_base_url + track

    output_path = os.path.splitext(json_path)[0] + " - updated.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated JSON saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fill_urls.py <input_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    fill_missing_data(input_file)
