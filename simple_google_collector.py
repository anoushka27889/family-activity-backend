# Fixed Google Places Collector - Simple and Reliable
# This version uses basic text search without complex place details calls

import requests
import sqlite3
import json
import os
from datetime import datetime
import time

class SimpleGooglePlacesCollector:
    def __init__(self, db_path: str = 'activities.db'):
        self.db_path = db_path
        self.api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def collect_real_places(self):
        """Collect real places using simple text search - more reliable"""
        
        if not self.api_key:
            return {"error": "No API key found"}
        
        # Simple searches that work reliably
        searches = [
            "children museums Berkeley California",
            "family parks San Francisco California", 
            "kids activities Oakland California",
            "playgrounds Berkeley California",
            "aquarium San Francisco California",
            "zoo Oakland California",
            "libraries Berkeley California",
            "science museums San Francisco California"
        ]
        
        collected_places = []
        
        for search_query in searches:
            try:
                print(f"Searching for: {search_query}")
                places = self.search_places(search_query)
                
                for place in places:
                    if self.is_family_friendly(place):
                        enhanced_place = self.enhance_place_data(place)
                        if enhanced_place:
                            self.save_place_to_db(enhanced_place)
                            collected_places.append(enhanced_place['name'])
                
                # Rate limiting - be nice to Google
                time.sleep(2)
                
            except Exception as e:
                print(f"Error with search '{search_query}': {e}")
                continue
        
        return {
            "success": True,
            "message": f"Collected {len(collected_places)} real places",
            "places": collected_places
        }
    
    def search_places(self, query):
        """Basic text search - most reliable Google Places API call"""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        params = {
            'query': query,
            'key': self.api_key,
            'type': 'point_of_interest'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] != 'OK':
            print(f"API Error: {data['status']} - {data.get('error_message', 'Unknown error')}")
            return []
        
        return data.get('results', [])[:5]  # Limit to 5 results per search
    
    def is_family_friendly(self, place):
        """Check if place is likely family-friendly"""
        name = place.get('name', '').lower()
        types = place.get('types', [])
        
        # Family-friendly keywords
        family_keywords = [
            'children', 'kids', 'family', 'playground', 'park', 'museum', 
            'library', 'aquarium', 'zoo', 'science', 'discovery', 'nature'
        ]
        
        # Family-friendly place types
        family_types = [
            'museum', 'park', 'library', 'aquarium', 'zoo', 'amusement_park',
            'tourist_attraction', 'point_of_interest'
        ]
        
        # Check name for family keywords
        if any(keyword in name for keyword in family_keywords):
            return True
        
        # Check types
        if any(place_type in family_types for place_type in types):
            return True
        
        return False
    
    def enhance_place_data(self, place):
        """Add rich data to place information"""
        try:
            # Extract basic info that's reliable
            name = place.get('name', 'Unknown Place')
            rating = place.get('rating', 4.0)
            user_ratings_total = place.get('user_ratings_total', 0)
            formatted_address = place.get('formatted_address', '')
            place_id = place.get('place_id', '')
            
            # Get geometry
            geometry = place.get('geometry', {})
            location = geometry.get('location', {})
            latitude = location.get('lat')
            longitude = location.get('lng')
            
            # Determine activity type from place types
            place_types = place.get('types', [])
            activity_type = self.determine_activity_type(place_types, name)
            
            # Estimate pricing from place types and name
            cost_info = self.estimate_cost(place_types, name)
            
            # Generate realistic tags
            tags = self.generate_tags(place_types, name)
            
            # Extract city from address
            city = self.extract_city(formatted_address)
            
            enhanced_place = {
                'name': name,
                'description': f"Family-friendly {activity_type} venue in {city}. {self.generate_description(name, place_types)}",
                'activity_type': activity_type,
                'rating': rating,
                'review_count': user_ratings_total,
                'address': formatted_address,
                'city': city,
                'latitude': latitude,
                'longitude': longitude,
                'place_id': place_id,
                'cost_category': cost_info['category'],
                'price_min': cost_info.get('min_price'),
                'price_max': cost_info.get('max_price'),
                'tags': tags,
                'source': 'google_places',
                'is_open_now': place.get('opening_hours', {}).get('open_now', True),
                'google_types': place_types
            }
            
            return enhanced_place
            
        except Exception as e:
            print(f"Error enhancing place data: {e}")
            return None
    
    def determine_activity_type(self, place_types, name):
        """Determine activity type from place data"""
        name_lower = name.lower()
        
        if any(t in place_types for t in ['museum', 'library']):
            return 'educational'
        elif any(t in place_types for t in ['park', 'playground']) or 'park' in name_lower:
            return 'outdoor'
        elif any(t in place_types for t in ['aquarium', 'zoo']):
            return 'educational'
        elif 'amusement' in name_lower or 'fun' in name_lower:
            return 'recreational'
        else:
            return 'recreational'
    
    def estimate_cost(self, place_types, name):
        """Estimate cost based on place type"""
        name_lower = name.lower()
        
        # Free places
        if any(t in place_types for t in ['park', 'library']) or 'park' in name_lower or 'library' in name_lower:
            return {'category': 'free', 'min_price': 0, 'max_price': 0}
        
        # Educational venues - usually have admission
        elif any(t in place_types for t in ['museum', 'aquarium', 'zoo']):
            return {'category': 'medium', 'min_price': 15, 'max_price': 25}
        
        # Everything else
        else:
            return {'category': 'low', 'min_price': 5, 'max_price': 15}
    
    def generate_tags(self, place_types, name):
        """Generate relevant tags"""
        tags = []
        name_lower = name.lower()
        
        # Type-based tags
        if 'museum' in place_types:
            tags.extend(['indoor', 'educational', 'rainy_day'])
        if 'park' in place_types or 'park' in name_lower:
            tags.extend(['outdoor', 'nature', 'playground'])
        if 'library' in place_types or 'library' in name_lower:
            tags.extend(['indoor', 'educational', 'free', 'reading'])
        if any(t in place_types for t in ['aquarium', 'zoo']):
            tags.extend(['animals', 'educational'])
        
        # Always add family-friendly tag
        tags.append('family_friendly')
        
        # Age-appropriate tags based on name
        if any(word in name_lower for word in ['children', 'kids']):
            tags.append('kid_focused')
        
        return list(set(tags))  # Remove duplicates
    
    def extract_city(self, address):
        """Extract city from formatted address"""
        if not address:
            return 'Unknown'
        
        # Simple extraction - look for known cities
        known_cities = ['Berkeley', 'San Francisco', 'Oakland', 'San Jose', 'Sausalito']
        
        for city in known_cities:
            if city in address:
                return city
        
        # Fallback - try to extract from address format
        parts = address.split(', ')
        if len(parts) >= 2:
            return parts[-3] if len(parts) > 2 else parts[-2]
        
        return 'Bay Area'
    
    def generate_description(self, name, place_types):
        """Generate a nice description"""
        descriptions = {
            'museum': 'Explore fascinating exhibits and interactive displays.',
            'park': 'Enjoy outdoor activities and beautiful natural surroundings.',
            'library': 'Discover books, programs, and educational activities.',
            'aquarium': 'Marvel at marine life and underwater worlds.',
            'zoo': 'Meet amazing animals from around the world.'
        }
        
        for place_type in place_types:
            if place_type in descriptions:
                return descriptions[place_type]
        
        return 'A wonderful family destination with activities for all ages.'
    
    def save_place_to_db(self, place_data):
        """Save place to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert activity
            cursor.execute('''
                INSERT OR REPLACE INTO activities 
                (title, description, activity_type, cost_category, price_min, price_max,
                 rating, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                place_data['name'],
                place_data['description'],
                place_data['activity_type'],
                place_data['cost_category'],
                place_data['price_min'],
                place_data['price_max'],
                place_data['rating'],
                datetime.now(),
                datetime.now()
            ))
            
            activity_id = cursor.lastrowid
            
            # Insert venue
            cursor.execute('''
                INSERT OR REPLACE INTO venues 
                (name, address, city, latitude, longitude, rating, 
                 google_place_id, venue_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                place_data['name'],
                place_data['address'],
                place_data['city'],
                place_data['latitude'],
                place_data['longitude'],
                place_data['rating'],
                place_data['place_id'],
                place_data['activity_type'],
                datetime.now(),
                datetime.now()
            ))
            
            venue_id = cursor.lastrowid
            
            # Link activity to venue
            cursor.execute('''
                INSERT OR IGNORE INTO activity_venues (activity_id, venue_id)
                VALUES (?, ?)
            ''', (activity_id, venue_id))
            
            # Save tags
            for tag_name in place_data['tags']:
                # Get or create tag
                cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                tag_result = cursor.fetchone()
                
                if tag_result:
                    tag_id = tag_result[0]
                else:
                    cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = cursor.lastrowid
                
                # Link activity to tag
                cursor.execute('''
                    INSERT OR IGNORE INTO activity_tags (activity_id, tag_id)
                    VALUES (?, ?)
                ''', (activity_id, tag_id))
            
            conn.commit()
            print(f"Saved: {place_data['name']}")
            
        except Exception as e:
            print(f"Error saving place {place_data['name']}: {e}")
            conn.rollback()
        finally:
            conn.close()

# Main function to run collection
def run_simple_google_collection():
    """Run the simplified Google Places collection"""
    collector = SimpleGooglePlacesCollector()
    result = collector.collect_real_places()
    return result

if __name__ == "__main__":
    result = run_simple_google_collection()
    print(json.dumps(result, indent=2))
