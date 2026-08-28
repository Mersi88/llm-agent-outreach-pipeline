from dotenv import load_dotenv
import googlemaps
import anthropic
import os
import json
from datetime import datetime

load_dotenv()

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def search_businesses(city, business_type):
    print(f"🔍 Searching for {business_type} in {city}...")
    
    results = gmaps.places(
        query=f"{business_type} in {city} Ontario Canada",
        type="establishment"
    )
    
    return results.get("results", [])

def has_website(place):
    try:
        details = gmaps.place(place["place_id"], fields=["website"])
        website = details.get("result", {}).get("website", None)
        if website:
            # Verify the website actually loads
            import requests
            try:
                response = requests.get(website, timeout=5)
                if response.status_code == 200:
                    return website
            except:
                return None
        return None
    except:
        return None

def scout_city(city, niches):
    all_leads = []
    
    for niche in niches:
        businesses = search_businesses(city, niche)
        
        for business in businesses:
            rating = business.get("rating", 0)
            review_count = business.get("user_ratings_total", 0)
            
            # Only keep quality businesses
            if rating >= 4.0 and 10 <= review_count <= 200:
                website = has_website(business)
                
                lead = {
                    "business_name": business.get("name"),
                    "address": business.get("formatted_address"),
                    "rating": rating,
                    "review_count": review_count,
                    "has_website": bool(website),
                    "website": website,
                    "place_id": business.get("place_id"),
                    "niche": niche,
                    "city": city,
                    "scraped_at": datetime.now().isoformat()
                }
                
                # Only add if no website or outdated
                if not website:
                    all_leads.append(lead)
                    print(f"✅ Found: {lead['business_name']} — No website — {rating}⭐ ({review_count} reviews)")
    
    return all_leads

# Run the scout
gta_cities = ["Scarborough", "Mississauga", "Brampton", "North York", "Etobicoke"]

niches = [
    # High value - most likely to pay
    "immigration consultant",
    "immigration lawyer",
    
    # Trades - understand ROI
    "handyman",
    "general contractor",
    "plumber",
    "electrician",
    "roofer",
    "painter",
    "hvac",
    
    # Food - catering and events money
    "ethnic restaurant",
    "catering company",
    
    # Personal brand - younger and tech savvy
    "personal trainer",
    "event photographer",
    "videographer",
]

all_leads = []

for city in gta_cities:
    leads = scout_city(city, niches)
    all_leads.extend(leads)

# Save results
os.makedirs("leads", exist_ok=True)
with open("leads/raw_leads.json", "w") as f:
    json.dump(all_leads, f, indent=2)

print(f"\n🎯 Total leads found: {len(all_leads)}")
print("📁 Saved to leads/raw_leads.json")