from dotenv import load_dotenv
import anthropic
import json
import os

load_dotenv()

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def diagnose_lead(lead):
    print(f"🧠 Diagnosing {lead['business_name']}...")

    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an expert at selling websites to small businesses in the Greater Toronto Area.

Analyze this business and create a pitch package:

Business: {lead['business_name']}
Type: {lead['niche']}
Location: {lead['city']}, Ontario
Rating: {lead['rating']} stars
Reviews: {lead['review_count']} Google reviews
Has Website: {lead['has_website']}

Return ONLY a JSON object with these exact fields:
{{
    "diagnosis": "50 word max explanation of why they need a website",
    "hero_angle": "the single strongest selling point for their specific business",
    "tone": "one word: warm OR professional OR casual OR direct",
    "cold_message": "personalized outreach message under 70 words, no AI buzzwords, must include business name, must have clear call to action",
    "contact_channel": "one of: email OR instagram_dm OR facebook_dm OR sms",
    "subject_line": "email subject line if contact channel is email, otherwise null"
}}

Rules for cold_message:
- Under 70 words
- No words like: leverage, synergy, innovative, tailored, cutting-edge
- Must sound human
- Must mention their review count or rating
- End with a question or clear next step"""
            }
        ]
    )

    raw = response.content[0].text
    
    # Clean and parse JSON
    clean = raw.replace("```json", "").replace("```", "").strip()
    diagnosis = json.loads(clean)
    
    # Add original lead info
    diagnosis["business_name"] = lead["business_name"]
    diagnosis["address"] = lead["address"]
    diagnosis["niche"] = lead["niche"]
    diagnosis["city"] = lead["city"]
    diagnosis["rating"] = lead["rating"]
    diagnosis["review_count"] = lead["review_count"]
    diagnosis["place_id"] = lead.get("place_id", "")
    
    return diagnosis

# Load leads
with open("leads/raw_leads.json", "r") as f:
    leads = json.load(f)

# Load already-diagnosed leads so we don't re-spend API calls on them
os.makedirs("leads", exist_ok=True)
if os.path.exists("leads/diagnosed_leads.json"):
    with open("leads/diagnosed_leads.json", "r") as f:
        diagnosed = json.load(f)
else:
    diagnosed = []

already_diagnosed_ids = {d.get("place_id") for d in diagnosed if d.get("place_id")}
leads_to_diagnose = [
    lead for lead in leads
    if lead.get("place_id") not in already_diagnosed_ids
]

skipped = len(leads) - len(leads_to_diagnose)
print(f"📋 Diagnosing {len(leads_to_diagnose)} new leads ({skipped} already diagnosed, skipped)...\n")

diagnosed_count_before_run = len(diagnosed)
failed = []

for lead in leads_to_diagnose:
    try:
        result = diagnose_lead(lead)
        diagnosed.append(result)
        print(f"✅ {lead['business_name']}")
        print(f"   📝 {result['cold_message'][:60]}...")
        print(f"   📱 Channel: {result['contact_channel']}\n")
    except Exception as e:
        print(f"❌ Failed: {lead['business_name']} — {e}\n")
        failed.append(lead)

# Save results
with open("leads/diagnosed_leads.json", "w") as f:
    json.dump(diagnosed, f, indent=2)

print(f"✅ Newly diagnosed: {len(diagnosed) - diagnosed_count_before_run}")
print(f"❌ Failed: {len(failed)}")
print(f"📁 Total in leads/diagnosed_leads.json: {len(diagnosed)}")