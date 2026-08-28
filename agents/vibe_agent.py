from dotenv import load_dotenv
import anthropic
import googlemaps
import requests
import base64
import json
import os

load_dotenv()

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

def detect_image_media_type(data):
    """Detect image media type from magic bytes, defaulting to JPEG"""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"

def fetch_business_photos(place_id, max_photos=4):
    """Fetch photos from Google Maps for a business"""
    print(f"📸 Fetching photos...")
    
    details = gmaps.place(
        place_id,
        fields=["photo", "name"]
    )
    
    photos = details.get("result", {}).get("photos", [])
    
    if not photos:
        print("⚠️  No photos found")
        return []
    
    photo_data = []
    for photo in photos[:max_photos]:
        try:
            photo_ref = photo["photo_reference"]
            url = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=800"
                f"&photo_reference={photo_ref}"
                f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
            )
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                media_type = detect_image_media_type(response.content)
                img_base64 = base64.b64encode(
                    response.content
                ).decode()
                photo_data.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_base64
                    }
                })
                print(f"✅ Photo {len(photo_data)} loaded")
        except Exception as e:
            print(f"⚠️  Skipped a photo: {e}")
    
    return photo_data

def analyze_vibe(lead):
    """Analyze business photos and extract unique identity"""
    print(f"\n🎨 Analyzing vibe for {lead['business_name']}...")
    
    place_id = lead.get("place_id", "")
    if not place_id:
        print("⚠️  No place_id — using niche defaults")
        return None
    
    # Fetch photos
    photo_data = fetch_business_photos(place_id)
    
    if not photo_data:
        print("⚠️  No photos available — using niche defaults")
        return None
    
    # Build message with photos + analysis request
    content = photo_data + [{
        "type": "text",
        "text": f"""You are analyzing photos of a real local business to understand 
their unique identity before building their website.

Business: {lead['business_name']}
Type: {lead['niche']}
City: {lead['city']}, Ontario, Canada
Google Rating: {lead['rating']} stars from {lead['review_count']} reviews

Look carefully at these photos and return ONLY a JSON object:
{{
    "vibe": "2-3 sentences describing the real atmosphere and identity of this business based on the photos",
    "cultural_identity": "specific cultural, community, or regional identity visible in photos — be specific",
    "dominant_colours": "colours you actually see in the photos — food colours, decor, branding",
    "colour_palette": "suggested website hex colours that match their actual identity",
    "headline_tone": "one of: warm / bold / celebratory / professional / community / rustic / modern",
    "unique_angle": "what makes THIS business different from a generic business in their niche",
    "hero_headline": "a compelling website headline that captures their real identity — NOT generic",
    "subtext": "supporting line under the headline — specific to what you see",
    "what_to_avoid": "what generic website templates get wrong about this specific business",
    "section_suggestions": "sections that make sense for THIS business specifically"
}}

Be specific. If you see South Asian sweets — say that.
If you see Caribbean food — say that.
If you see a family-run shop feel — say that.
Generic answers are useless. Specific observations build great websites."""
    }]
    
    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}]
    )
    
    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    
    try:
        vibe = json.loads(clean)
        return vibe
    except Exception as e:
        print(f"❌ Failed to parse vibe: {e}")
        return None

def run_vibe_agent():
    """Run vibe analysis on all diagnosed leads"""
    
    with open("leads/diagnosed_leads.json", "r") as f:
        leads = json.load(f)
    
    print(f"🎨 Running Vibe Agent on {len(leads)} leads...\n")
    
    results = []
    failed = 0
    
    for lead in leads:
        try:
            vibe = analyze_vibe(lead)
            
            if vibe:
                lead["vibe"] = vibe
                print(f"✅ {lead['business_name']}")
                print(f"   Identity: {vibe['cultural_identity']}")
                print(f"   Headline: {vibe['hero_headline']}")
                print(f"   Avoid: {vibe['what_to_avoid']}\n")
            else:
                lead["vibe"] = None
                print(f"⚠️  {lead['business_name']} — no photos, using defaults\n")
            
            results.append(lead)
            
        except Exception as e:
            print(f"❌ Failed: {lead['business_name']} — {e}\n")
            lead["vibe"] = None
            results.append(lead)
            failed += 1
    
    # Save updated leads with vibe data
    with open("leads/diagnosed_leads.json", "w") as f:
        json.dump(results, f, indent=2)
    
    successful = len([r for r in results if r.get("vibe")])
    
    print(f"✅ Vibe analyzed: {successful}")
    print(f"⚠️  No photos: {failed}")
    print(f"📁 Saved to leads/diagnosed_leads.json")

# Test on your 3 target businesses first
def test_vibe(business_name):
    """Test vibe agent on a single business by name"""
    with open("leads/diagnosed_leads.json", "r") as f:
        leads = json.load(f)
    
    lead = next(
        (l for l in leads if business_name.lower() in l["business_name"].lower()), 
        None
    )
    
    if not lead:
        print(f"❌ Business '{business_name}' not found in leads")
        return
    
    vibe = analyze_vibe(lead)
    
    if vibe:
        print("\n" + "="*50)
        print("🎨 VIBE REPORT")
        print("="*50)
        for key, value in vibe.items():
            print(f"\n{key.upper()}:")
            print(f"  {value}")
    else:
        print("❌ Could not analyze vibe")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        business_name = " ".join(sys.argv[1:])
        test_vibe(business_name)
    else:
        print("Usage: python agents/vibe_agent.py <business name>")
