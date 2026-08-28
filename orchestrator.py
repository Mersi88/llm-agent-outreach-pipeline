from dotenv import load_dotenv
import os
import json
import sys
from datetime import datetime

load_dotenv()

CALENDLY_LINK = "https://calendly.com/marsimohidigital/15-min-website-preview-call"
SAFE_MODE = True  # Change to False when ready for real sends

print("=" * 60)
print("🤖 GTA WEB AGENCY — DAILY PIPELINE")
print(f"📅 {datetime.now().strftime('%A %B %d, %Y — %I:%M %p')}")
print("=" * 60)

# ── STEP 1: SCOUT ──────────────────────────────────────────
print("\n📍 STEP 1: SCOUT — Finding new leads...")
sys.path.insert(0, "agents")
import scout_agent
print("✅ Scout complete")

# ── STEP 2: DIAGNOSER ──────────────────────────────────────
print("\n📍 STEP 2: DIAGNOSER — Writing cold messages...")
import diagnoser_agent
print("✅ Diagnoser complete")

import builder_a_agent
import checker_agent

# ── STEP 3: PICK TOP 5 ─────────────────────────────────────
print("\n📍 STEP 3: Selecting top 5 leads for today...")

with open("leads/diagnosed_leads.json", "r") as f:
    leads = json.load(f)

top5 = sorted(leads, key=lambda x: x["review_count"], reverse=True)[:5]

os.makedirs("leads", exist_ok=True)
with open("leads/todays_top5.json", "w") as f:
    json.dump(top5, f, indent=2)

print(f"✅ Top 5 selected:")
for lead in top5:
    print(f"   → {lead['business_name']} ({lead['review_count']} reviews, {lead['city']})")

# ── STEP 4: BUILDER A ──────────────────────────────────────
print("\n📍 STEP 4: BUILDER A — Building mockup websites...")

built_urls = []
for lead in top5:
    try:
        url = builder_a_agent.build_mockup(lead)
        if url is None:
            continue  # lead already has a real website — skipped, not built
        lead["mockup_url"] = url
        built_urls.append({"business_name": lead["business_name"], "url": url})
    except Exception as e:
        print(f"❌ Builder failed for {lead['business_name']}: {e}")

with open("leads/todays_top5.json", "w") as f:
    json.dump(top5, f, indent=2)

# leads carries the same dict objects as top5, so has_real_website flags
# set by build_mockup are already reflected here — persist them.
with open("leads/diagnosed_leads.json", "w") as f:
    json.dump(leads, f, indent=2)

# ── STEP 5: CHECKER ────────────────────────────────────────
print("\n📍 STEP 5: CHECKER — Validating messages...")

approved = []
for lead in top5:
    try:
        result = checker_agent.check_message(
            message=lead["cold_message"],
            business_name=lead["business_name"],
            review_count=lead["review_count"],
            contact_channel=lead["contact_channel"]
        )
        if result["approved"]:
            approved.append(lead)
            print(f"✅ {lead['business_name']}")
        elif result.get("improved_message"):
            lead["cold_message"] = result["improved_message"]
            approved.append(lead)
            print(f"✅ {lead['business_name']} (auto-fixed)")
        else:
            print(f"❌ {lead['business_name']} — skipped")
    except Exception as e:
        approved.append(lead)
        print(f"⚠️  {lead['business_name']} — kept anyway")

# ── STEP 6: HUMAN APPROVAL ─────────────────────────────────
print("\n📍 STEP 6: YOUR APPROVAL NEEDED")
print("=" * 60)

for i, lead in enumerate(approved):
    print(f"\n[{i+1}] {lead['business_name']}")
    print(f"    Channel : {lead['contact_channel']}")
    print(f"    Mockup  : {lead.get('mockup_url', 'not built')}")
    print(f"    Message : {lead['cold_message'][:120]}...")

print()
answer = input("👤 Send these messages? (y/n): ").strip().lower()

if answer != "y":
    print("⏸️  Cancelled. Everything saved to leads/todays_top5.json")
    exit()

# ── STEP 7: PITCHER ────────────────────────────────────────
print("\n📍 STEP 7: PITCHER — Sending messages...")

results = []
for lead in approved:
    channel = lead.get("contact_channel", "email")
    message = f"{lead['cold_message']}\n\nBook a quick 15-min call: {CALENDLY_LINK}"

    if SAFE_MODE:
        print(f"📤 [SAFE MODE] {channel.upper()} → {lead['business_name']}")
        status = "queued"
    else:
        print(f"📤 SENDING {channel.upper()} → {lead['business_name']}")
        status = "sent"

    results.append({
        "business_name": lead["business_name"],
        "channel": channel,
        "message": message,
        "mockup_url": lead.get("mockup_url", ""),
        "status": status,
        "timestamp": datetime.now().isoformat()
    })

# ── DAILY LOG ──────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
log_file = f"logs/daily_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(log_file, "w") as f:
    json.dump({
        "date": datetime.now().isoformat(),
        "total_leads": len(leads),
        "top5": len(top5),
        "mockups_built": len(built_urls),
        "approved": len(approved),
        "sent": len(results),
        "safe_mode": SAFE_MODE,
        "results": results
    }, f, indent=2)

print("\n" + "=" * 60)
print("✅ DAILY PIPELINE COMPLETE")
print(f"📊 Leads found    : {len(leads)}")
print(f"🏗️  Mockups built  : {len(built_urls)}")
print(f"✅ Approved        : {len(approved)}")
print(f"📤 Messages sent  : {len(results)}")
print(f"📁 Log saved      : {log_file}")
print("=" * 60)