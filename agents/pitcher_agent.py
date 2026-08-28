from dotenv import load_dotenv
import json
import os
from datetime import datetime

load_dotenv()

# ============================================
# SAFE MODE — set to True to actually send
# Set to False to just preview what would send
# ============================================
SAFE_MODE = True
DAILY_LIMIT = 10  # max messages per run
CALENDLY_LINK = "https://calendly.com/marsimohidigital/15-min-website-preview-call"

def send_email(lead, message):
    if SAFE_MODE:
        print(f"   📧 [SAFE MODE] Would send EMAIL to: {lead['business_name']}")
        print(f"   Subject: {lead.get('subject_line', 'Quick question about your online presence')}")
        print(f"   Message: {message[:80]}...")
        return True
    else:
        # Real SendGrid sending goes here later
        pass

def send_sms(lead, message):
    if SAFE_MODE:
        print(f"   📱 [SAFE MODE] Would send SMS to: {lead['business_name']}")
        print(f"   Message: {message[:80]}...")
        return True
    else:
        # Real Twilio sending goes here later
        pass

def send_instagram_dm(lead, message):
    if SAFE_MODE:
        print(f"   📸 [SAFE MODE] Would send INSTAGRAM DM to: {lead['business_name']}")
        print(f"   Message: {message[:80]}...")
        return True
    else:
        # Real Instagram API goes here later
        pass

def add_calendly(message):
    return f"{message}\n\nBook a quick 15-min call: {CALENDLY_LINK}"

def pitch_lead(lead):
    channel = lead.get("contact_channel", "email")
    message = lead.get("cold_message", "")

    # Add Calendly link
    message_with_link = add_calendly(message)

    print(f"\n🚀 Pitching: {lead['business_name']}")
    print(f"   Channel: {channel}")

    if channel == "email":
        success = send_email(lead, message_with_link)
    elif channel == "sms":
        success = send_sms(lead, message_with_link)
    elif channel == "instagram_dm":
        success = send_instagram_dm(lead, message_with_link)
    else:
        success = send_email(lead, message_with_link)

    return {
        "business_name": lead["business_name"],
        "channel": channel,
        "message": message_with_link,
        "status": "sent" if success else "failed",
        "timestamp": datetime.now().isoformat(),
        "safe_mode": SAFE_MODE
    }

# Load approved leads
with open("leads/approved_leads.json", "r") as f:
    leads = json.load(f)

print(f"📋 Loaded {len(leads)} approved leads")
print(f"📤 Will pitch top {DAILY_LIMIT} leads")
print(f"🔒 Safe mode: {'ON (preview only)' if SAFE_MODE else 'OFF (real sends)'}")
print("=" * 50)

# Pick top leads by review count
top_leads = sorted(leads, key=lambda x: x["review_count"], reverse=True)[:DAILY_LIMIT]

# Send to each
results = []
for lead in top_leads:
    result = pitch_lead(lead)
    results.append(result)

# Save log
os.makedirs("logs", exist_ok=True)
with open("logs/sent_messages.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 50)
print(f"✅ Done! Pitched {len(results)} businesses")
print(f"📁 Log saved to logs/sent_messages.json")

# Summary by channel
channels = {}
for r in results:
    ch = r["channel"]
    channels[ch] = channels.get(ch, 0) + 1

print("\n📊 By channel:")
for ch, count in channels.items():
    print(f"   {ch}: {count}")