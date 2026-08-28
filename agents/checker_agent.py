from dotenv import load_dotenv
import anthropic
import json
import os

load_dotenv()

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def check_message(message, business_name, review_count, contact_channel):
    print(f"🔍 Checking message for {business_name}...")

    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": f"""You are a cold outreach quality checker for a web agency targeting small businesses in Toronto.

Evaluate this cold message and return ONLY a JSON object.

Business: {business_name}
Review count: {review_count}
Channel: {contact_channel}

Message to check:
\"\"\"{message}\"\"\"

Check ALL of these:
1. Under 70 words? (count carefully)
2. Sounds human, not like AI?
3. No buzzwords? (leverage, synergy, innovative, tailored, cutting-edge, game-changer, revolutionize)
4. Mentions the business name?
5. Mentions their review count or rating?
6. Ends with a clear question or next step?
7. Appropriate for the channel? (SMS should be shorter and more casual, email can be slightly longer)
8. Does NOT include a website link or URL?
9. Does NOT sound like a scam or phishing attempt?

Return ONLY this JSON, nothing else:
{{
    "approved": true or false,
    "word_count": number,
    "issues": ["list of issues if rejected, empty if approved"],
    "improved_message": "only include if rejected — a fixed version under 70 words"
}}"""
            }
        ]
    )

    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def check_all_messages():
    with open("leads/diagnosed_leads.json", "r") as f:
        leads = json.load(f)

    approved = []
    rejected = []

    for lead in leads:
        try:
            result = check_message(
                message=lead["cold_message"],
                business_name=lead["business_name"],
                review_count=lead["review_count"],
                contact_channel=lead["contact_channel"]
            )

            lead["checker_result"] = result

            if result["approved"]:
                approved.append(lead)
                print(f"✅ APPROVED: {lead['business_name']} ({result['word_count']} words)")
            else:
                rejected.append(lead)
                print(f"❌ REJECTED: {lead['business_name']}")
                for issue in result["issues"]:
                    print(f"   → {issue}")
                if result.get("improved_message"):
                    lead["cold_message"] = result["improved_message"]
                    lead["checker_result"]["approved"] = True
                    approved.append(lead)
                    print(f"   ✅ Auto-fixed and approved")

        except Exception as e:
            print(f"⚠️  Error checking {lead['business_name']}: {e}")
            approved.append(lead)

    # Save results
    os.makedirs("leads", exist_ok=True)
    with open("leads/approved_leads.json", "w") as f:
        json.dump(approved, f, indent=2)

    print(f"\n📊 RESULTS:")
    print(f"✅ Approved: {len(approved)}")
    print(f"❌ Rejected: {len(rejected)}")
    print(f"📁 Saved to leads/approved_leads.json")

if __name__ == "__main__":
    check_all_messages()