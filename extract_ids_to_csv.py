import json
import csv

# Input and output filenames
input_file = "category list.json"
output_file = "category_ids.csv"

# Load the JSON data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract IDs and Titles
entries = data.get("data", [])
rows = [(entry.get("title", "").strip(), entry.get("id")) for entry in entries if "id" in entry and "title" in entry]

# Write to CSV
with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "id"])  # Header
    writer.writerows(rows)

print(f"✅ Extracted {len(rows)} entries to {output_file}")
