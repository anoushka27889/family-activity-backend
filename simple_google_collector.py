import requests
import sqlite3
import json
import os
from datetime import datetime

def simple_google_collection():
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    
    if not api_key:
        return {"error": "No API key"}
    
    # Simple text searches that usually work
    searches = [
        "family museums Berkeley CA",
        "children playground San Francisco CA", 
        "kids activities Oakland CA"
    ]
    
    results = []
    
    for search in searches:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                'query': search,
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                for place in data['results'][:3]:  # Just first 3 results
                    place_info = {
                        'name': place.get('name'),
                        'rating': place.get('rating', 4.0),
                        'address': place.get('formatted_address'),
                        'types': place.get('types', [])
                    }
                    results.append(place_info)
        except Exception as e:
            print(f"Error with search {search}: {e}")
    
    return {"success": True, "places_found": len(results), "places": results}

# Test function
if __name__ == "__main__":
    result = simple_google_collection()
    print(json.dumps(result, indent=2))
