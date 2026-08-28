import json
from collections import Counter

with open("leads/raw_leads.json", "r") as f:
    leads = json.load(f)

print(f"\n📊 TOTAL LEADS: {len(leads)}\n")

# Count by niche
niches = Counter(lead["niche"] for lead in leads)
print("🏷️  LEADS BY NICHE:")
for niche, count in niches.most_common():
    print(f"   {count:3} — {niche}")

# Count by city
cities = Counter(lead["city"] for lead in leads)
print("\n🏙️  LEADS BY CITY:")
for city, count in cities.most_common():
    print(f"   {count:3} — {city}")

# Top 10 leads by review count
print("\n⭐ TOP 10 LEADS BY REVIEWS:")
top = sorted(leads, key=lambda x: x["review_count"], reverse=True)[:10]
for lead in top:
    print(f"   {lead['review_count']:4} reviews — {lead['business_name']} ({lead['niche']}, {lead['city']})")