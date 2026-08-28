from dotenv import load_dotenv
import anthropic
import json
import os
import time

load_dotenv()
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXCLUDED_NICHE_KEYWORDS = [
    "nail salon", "nail spa", "beauty salon", "beauty spa", "hair salon",
    "spa", "esthetics", "waxing",
    "bar", "pub", "brewery", "brewpub", "liquor store", "wine store", "distillery",
    "casino", "gambling", "betting",
    "tattoo", "piercing",
]

def is_excluded_niche(niche):
    niche_lower = (niche or "").lower()
    return any(keyword in niche_lower for keyword in EXCLUDED_NICHE_KEYWORDS)

FOOD_NICHES_NEEDING_REVIEW = {"ethnic restaurant", "catering company"}

def classify_food_business(business_name, niche, address):
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": f"""Business name: "{business_name}"
Category: {niche}
Address: {address}

Based ONLY on the business name and category (no menu data available), does this business LIKELY prominently feature pork or alcohol as a core part of what it sells (e.g. a BBQ pork restaurant, a wine bar, a brewery-restaurant)?

Respond with exactly one word: likely, unlikely, or unclear."""
            }]
        )
        verdict = response.content[0].text.strip().lower()
        if "unclear" in verdict:
            return "unclear"
        elif "unlikely" in verdict:
            return "unlikely"
        elif "likely" in verdict:
            return "likely"
        return "unclear"
    except Exception as e:
        print(f"   ⚠️ classify failed for {business_name}: {e}")
        return "unclear"

with open("leads/diagnosed_leads.json", "r") as f:
    leads = json.load(f)

print(f"Loaded {len(leads)} leads.")

excluded_niche_hits = [l for l in leads if is_excluded_niche(l.get("niche", ""))]
if excluded_niche_hits:
    print(f"\n⛔ {len(excluded_niche_hits)} lead(s) are in a categorically excluded niche:")
    for l in excluded_niche_hits:
        print(f"   - {l['business_name']} ({l['niche']}, {l.get('city')})")
else:
    print("\n⛔ 0 leads in a categorically excluded niche (expected — those niches were never scouted).")

to_classify = [l for l in leads if l.get("niche") in FOOD_NICHES_NEEDING_REVIEW and "food_review_flag" not in l]
print(f"\n🔍 {len(to_classify)} lead(s) need pork/alcohol classification (niche = ethnic restaurant or catering company)...")

for i, lead in enumerate(to_classify, 1):
    flag = classify_food_business(lead["business_name"], lead["niche"], lead.get("address", ""))
    lead["food_review_flag"] = flag
    print(f"   [{i}/{len(to_classify)}] {lead['business_name']} → {flag}")
    time.sleep(0.5)

with open("leads/diagnosed_leads.json", "w") as f:
    json.dump(leads, f, indent=2)

flagged = [l for l in leads if l.get("food_review_flag") in ("likely", "unclear")]
print(f"\n🚩 {len(flagged)} total lead(s) flagged for manual pork/alcohol review before outreach:")
for l in flagged:
    print(f"   - {l['business_name']} ({l['niche']}, {l.get('city')}) — {l['food_review_flag']}")

print("\n✅ leads/diagnosed_leads.json updated in place. Backup at leads/diagnosed_leads.backup2.json.")
