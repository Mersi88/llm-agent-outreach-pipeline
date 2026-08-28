"""
One-off maintenance script: merges the orphaned raw_leads.json (scraped from
the EXPLORER root due to scout_agent.py being run from the wrong working
directory) into the real leads/raw_leads.json, deduplicating by place_id.

Usage: python3 merge_raw_leads.py
"""
import json
import shutil

PRIMARY = "leads/raw_leads.json"
ORPHANED = "../leads/raw_leads.json"
BACKUP = "leads/raw_leads.backup.json"


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    primary = load(PRIMARY)
    orphaned = load(ORPHANED)

    print(f"{PRIMARY}: {len(primary)} records")
    print(f"{ORPHANED}: {len(orphaned)} records")

    by_place_id = {}
    for record in primary + orphaned:
        place_id = record.get("place_id")
        if not place_id:
            continue
        existing = by_place_id.get(place_id)
        if existing is None or record.get("scraped_at", "") > existing.get("scraped_at", ""):
            by_place_id[place_id] = record

    merged = list(by_place_id.values())
    merged.sort(key=lambda r: r.get("scraped_at", ""))

    shutil.copy(PRIMARY, BACKUP)
    print(f"Backed up original {PRIMARY} -> {BACKUP}")

    with open(PRIMARY, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    print(f"Merged into {PRIMARY}: {len(merged)} unique leads (deduplicated by place_id)")


if __name__ == "__main__":
    main()
