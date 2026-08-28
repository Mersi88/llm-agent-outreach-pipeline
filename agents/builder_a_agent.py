from dotenv import load_dotenv
import anthropic
import requests
import os
import json
import io
import zipfile
import random

load_dotenv()

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
NETLIFY_TOKEN = os.getenv("NETLIFY_TOKEN")

import googlemaps
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

DESIGN_PROFILES = {
    "immigration consultant": {
        "colours": "deep navy #0a1628 and gold #c9a84c",
        "personality": "Law firm meets trusted advisor. Think clean serif fonts, formal layout, lots of white space, credential badges, professional headshots placeholder. Feels like you're in good hands.",
        "hero_style": "Centered, authoritative headline. Subtext about success rates. Two CTAs: Book Consultation and Call Now.",
        "sections": "Hero, Why Choose Us (credentials), Services, Success Stories, Book a Call"
    },
    "immigration lawyer": {
        "colours": "charcoal #1a1a2e and gold #c9a84c",
        "personality": "Serious law firm energy. Clean, minimal, trustworthy. Bar association badges. Professional and precise.",
        "hero_style": "Bold statement about winning cases or protecting futures. Very formal tone.",
        "sections": "Hero, Practice Areas, Attorney Profile, Client Results, Contact"
    },
    "personal trainer": {
        "colours": "pure black #000000 and electric blue #0066ff",
        "personality": "High energy gym aesthetic. Bold aggressive typography, before/after transformation energy, motivational language. Feels like a Nike ad.",
        "hero_style": "Full width dark hero, huge bold headline, transformation-focused CTA. High contrast.",
        "sections": "Hero, Transformation Results, Training Programs, Testimonials, Book Free Session"
    },
    "videographer": {
        "colours": "deep black #0d0d0d and warm amber #f5a623",
        "personality": "Film industry aesthetic. Cinematic, moody, portfolio-forward. Think film grain texture, widescreen ratios, subtle animations. Let the work speak.",
        "hero_style": "Full bleed dark hero with showreel CTA front and center. Minimal text, maximum impact.",
        "sections": "Hero, Portfolio Grid, Services, Client List, Book Your Date"
    },
    "event photographer": {
        "colours": "deep black #111111 and rose gold #b76e79",
        "personality": "Elegant and romantic. Wedding photographer energy. Soft, emotional, story-driven. Feels like flipping through a beautiful album.",
        "hero_style": "Emotional headline about capturing memories. Soft gradient overlay. Book Now prominent.",
        "sections": "Hero, Portfolio, Packages, Testimonials, Availability Calendar"
    },
    "ethnic restaurant": {
        "colours": "warm terracotta #c1440e and cream #fdf6ec",
        "personality": "Warm, inviting, family-owned feel. Rich colours, food photography placeholders, handwritten-style accents. Feels like walking into someone's home kitchen.",
        "hero_style": "Warm full-width hero with food-focused headline. Menu and Reserve CTAs.",
        "sections": "Hero, Menu Highlights, Our Story, Reviews, Visit Us"
    },
    "catering company": {
        "colours": "forest green #2d5016 and gold #d4af37",
        "personality": "Premium events feel. Corporate and elegant. Think high-end catering for weddings and galas. Sophisticated, not flashy.",
        "hero_style": "Elegant headline about unforgettable events. Get a Quote CTA prominent.",
        "sections": "Hero, Event Types, Menu Packages, Client Events, Request a Quote"
    },
    "handyman": {
        "colours": "dark navy #1a2744 and bright orange #ff6b00",
        "personality": "Reliable trades energy. No-nonsense, blue collar, trustworthy. Bold and direct. Feels like a truck decal come to life.",
        "hero_style": "Direct headline. What we fix, how fast, call now. Action-oriented.",
        "sections": "Hero, Services, Why Choose Us, Reviews, Get a Quote"
    },
    "general contractor": {
        "colours": "charcoal #2c2c2c and construction yellow #ffd700",
        "personality": "Professional construction company. Established, experienced, results-driven. Before/after project energy. Portfolio heavy.",
        "hero_style": "Strong headline about transforming homes. Free estimate CTA.",
        "sections": "Hero, Featured Projects, Services, Credentials, Free Estimate"
    },
    "plumber": {
        "colours": "deep blue #003366 and white #ffffff",
        "personality": "Emergency services feel. Fast, reliable, available 24/7. Red urgency accents for emergency CTA. Clear and direct.",
        "hero_style": "Emergency availability front and center. Call Now huge and prominent.",
        "sections": "Hero, Emergency Services, All Services, Reviews, Contact"
    },
    "electrician": {
        "colours": "black #111111 and electric yellow #ffe600",
        "personality": "Licensed and certified energy. Safety-forward, professional. Spark/lightning visual language. Feels established and trustworthy.",
        "hero_style": "Safety and certification front and center. Licensed badge prominent.",
        "sections": "Hero, Services, Certifications, Reviews, Book a Job"
    },
    "hvac": {
        "colours": "steel blue #4a90d9 and white #f8f9fa",
        "personality": "Clean, technical, reliable. Air and comfort focused. Seasonal maintenance energy. Feels like a company that shows up on time.",
        "hero_style": "Comfort and reliability headline. Emergency and seasonal service CTAs.",
        "sections": "Hero, Services, Maintenance Plans, Reviews, Book Service"
    },
    "roofer": {
        "colours": "slate grey #4a4a4a and red #cc0000",
        "personality": "Storm damage and protection energy. Tough, reliable, experienced. Before/after roof photos. Warranty-forward.",
        "hero_style": "Protection and warranty headline. Free inspection CTA prominent.",
        "sections": "Hero, Services, Our Work, Warranty, Free Inspection"
    },
    "painter": {
        "colours": "clean white #ffffff and deep teal #008080",
        "personality": "Transformation and beauty focused. Before/after energy. Colour swatches visual language. Feels creative and precise.",
        "hero_style": "Transformation headline. Free quote and portfolio CTAs.",
        "sections": "Hero, Before/After Gallery, Services, Colours We Love, Free Quote"
    },
}

def verify_no_real_website(lead):
    """Web search for the business to check whether it already has an
    independent website under its own domain — not a directory listing,
    review site, or social media page. This closes the gap where scout_agent.py
    only checks the Google Business Profile "website" field, which misses
    real sites that were never linked there.

    Mutates lead in place with has_real_website / existing_website_url /
    existing_website_check_reason, and returns has_real_website.
    """
    print(f"🔎 Checking for an existing website: {lead['business_name']}...")

    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"""Search the web for: "{lead['business_name']} {lead['city']}"

I need to know if this business has an independent website under its own domain — NOT a Google Business Profile, Yelp, Facebook, Instagram, LinkedIn, or other social media page, and NOT a third-party directory listing (Yellow Pages, BBB, Tripadvisor, etc.).

Return ONLY a JSON object with these exact fields:
{{
    "has_real_website": true or false,
    "url": "the website URL if one was found, otherwise null",
    "reasoning": "one sentence explaining what you found"
}}"""
        }]
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    raw = text_blocks[-1] if text_blocks else "{}"
    clean = raw.replace("```json", "").replace("```", "").strip()
    result = json.loads(clean)

    lead["has_real_website"] = result.get("has_real_website", False)
    lead["existing_website_url"] = result.get("url")
    lead["existing_website_check_reason"] = result.get("reasoning", "")
    return lead["has_real_website"]

def get_phone_number(place_id):
    try:
        details = gmaps.place(place_id, fields=["formatted_phone_number"])
        return details.get("result", {}).get("formatted_phone_number", "Call for info")
    except:
        return "Call for info"

def generate_website(lead):
    print(f"🎨 Generating website for {lead['business_name']}...")

    vibe = lead.get("vibe")

    if vibe:
        design_brief = f"""DESIGN PROFILE — derived from this specific business's real Google photos. Use this instead of a generic niche template:
Cultural/community identity: {vibe['cultural_identity']}
What makes them different from a generic business in this niche: {vibe['unique_angle']}
Website colour palette (use these colours, not generic niche colours): {vibe['colour_palette']}
Headline tone: {vibe['headline_tone']}
Sections to include (use these instead of a generic section list): {vibe['section_suggestions']}

Use this exact hero headline, do not invent your own: {vibe['hero_headline']}
Use this exact hero subtext, do not invent your own: {vibe['subtext']}

MUST AVOID: {vibe['what_to_avoid']}"""
    else:
        profile = DESIGN_PROFILES.get(lead["niche"], {
            "colours": "navy and white",
            "personality": "Professional and clean",
            "hero_style": "Bold headline with clear CTA",
            "sections": "Hero, Services, Reviews, Contact, Footer"
        })
        design_brief = f"""DESIGN PROFILE FOR THIS NICHE (no vibe data for this business — falling back to a niche template):
Colour scheme: {profile['colours']}
Personality: {profile['personality']}
Hero style: {profile['hero_style']}
Sections to include: {profile['sections']}"""

    phone = get_phone_number(lead.get("place_id", ""))
    address = lead.get("address", "Greater Toronto Area, Ontario")

    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=21000,
        messages=[
            {
                "role": "user",
                "content": f"""You are an expert web developer and designer.
Build a complete, beautiful, professional 1-page HTML website using Tailwind CSS CDN.

Business: {lead['business_name']}
Type: {lead['niche']}
City: {lead['city']}, Ontario, Canada
Address: {address}
Phone: {phone}
Rating: {lead['rating']} stars from {lead['review_count']} Google reviews
Hero angle: {lead['hero_angle']}
Tone: {lead['tone']}

{design_brief}

Technical requirements:
- Complete single HTML file
- Use ONLY: <script src="https://cdn.tailwindcss.com"></script>
- NO custom tailwind.config whatsoever
- Use inline styles for gradients and shadows
- Real address everywhere: {address}
- Real phone everywhere: {phone}
- Sample reviews clearly labelled as sample reviews
- Mobile first and fully responsive
- Return ONLY complete HTML starting with <!DOCTYPE html>
- No explanation, no markdown, just pure HTML

CRITICAL: This website must feel completely different from a 
generic template. The personality brief above defines the 
entire visual language. A plumber site should look NOTHING 
like an immigration consultant site. Make each one feel like 
it was custom designed specifically for that industry."""
            }
        ]
    )

    html = response.content[0].text

    # Clean in case Claude adds markdown
    if "```html" in html:
        html = html.split("```html")[1].split("```")[0].strip()
    elif "```" in html:
        html = html.split("```")[1].split("```")[0].strip()

    return html

def create_zip(html):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html)
        zf.writestr("_headers", "/*\n  Content-Type: text/html; charset=UTF-8\n")
    buffer.seek(0)
    return buffer.read()

def deploy_to_netlify(html, business_name):
    print(f"🚀 Deploying {business_name} to Netlify...")

    # Clean business name for site name
    site_name = business_name.lower()
    site_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in site_name)
    site_name = site_name.strip('-')[:30]
    site_name = f"{site_name}-{random.randint(1000,9999)}"

    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    # Create a new Netlify site
    site_response = requests.post(
        "https://api.netlify.com/api/v1/sites",
        headers=headers,
        json={"name": site_name}
    )

    if site_response.status_code not in [200, 201]:
        raise Exception(f"Failed to create site: {site_response.text}")

    site_id = site_response.json()["id"]
    site_url = site_response.json().get("ssl_url") or site_response.json().get("url")

    # Deploy the zip
    deploy_response = requests.post(
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
        headers={
            "Authorization": f"Bearer {NETLIFY_TOKEN}",
            "Content-Type": "application/zip"
        },
        data=create_zip(html)
    )

    if deploy_response.status_code not in [200, 201]:
        raise Exception(f"Failed to deploy: {deploy_response.text}")

    return site_url

def build_mockup(lead):
    if verify_no_real_website(lead):
        print(f"⏭️  Skipping {lead['business_name']}: already has a website "
              f"({lead.get('existing_website_url')}) — {lead.get('existing_website_check_reason')}")
        return None

    # Generate HTML
    html = generate_website(lead)

    # Save locally
    business_folder = f"clients/{lead['business_name'].replace(' ', '_')}"
    os.makedirs(business_folder, exist_ok=True)

    with open(f"{business_folder}/index.html", "w") as f:
        f.write(html)
    print(f"✅ HTML saved locally")

    # Deploy to Netlify
    live_url = deploy_to_netlify(html, lead['business_name'])

    # Save URL
    with open(f"{business_folder}/mockup_url.txt", "w") as f:
        f.write(live_url)

    print(f"✅ Live at: {live_url}")
    return live_url

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build mockup websites for leads")
    parser.add_argument(
        "--businesses",
        help="Comma-separated exact business_name values to build, instead of top 3 by review count"
    )
    parser.add_argument(
        "--place-ids",
        help="Comma-separated place_id values to build, instead of top 3 by review count"
    )
    args = parser.parse_args()

    # Load diagnosed leads
    with open("leads/diagnosed_leads.json", "r") as f:
        leads = json.load(f)

    if args.businesses:
        wanted = {name.strip().lower() for name in args.businesses.split(",")}
        top_leads = [l for l in leads if l.get("business_name", "").strip().lower() in wanted]
    elif args.place_ids:
        wanted = {pid.strip() for pid in args.place_ids.split(",")}
        top_leads = [l for l in leads if l.get("place_id") in wanted]
    else:
        # Pick top 3 by review count to test
        top_leads = sorted(leads, key=lambda x: x["review_count"], reverse=True)[:3]

    results = []
    for lead in top_leads:
        try:
            url = build_mockup(lead)
            if url is None:
                continue  # lead already has a real website — skipped, not built
            results.append({
                "business_name": lead["business_name"],
                "url": url
            })
        except Exception as e:
            print(f"❌ Failed: {lead['business_name']} — {e}")

    # leads still holds the same dict objects as top_leads, so has_real_website
    # flags set by build_mockup are already reflected here — persist them.
    with open("leads/diagnosed_leads.json", "w") as f:
        json.dump(leads, f, indent=2)

    print("\n🎯 RESULTS:")
    for r in results:
        print(f"✅ {r['business_name']} → {r['url']}")