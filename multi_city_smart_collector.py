# Multi-City Expanded Collector with Smart Duration Logic
# Comprehensive data collection for all Bay Area cities with duration intelligence

import requests
import sqlite3
import json
import os
from datetime import datetime
import time

class MultiCitySmartCollector:
    def __init__(self, db_path: str = 'activities.db'):
        self.db_path = db_path
        self.api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        
        # City configurations with specific search strategies
        self.cities_config = {
            'Berkeley': {
                'coordinates': {'lat': 37.8715, 'lng': -122.2730},
                'radius': 8000,  # 8km radius
                'specific_searches': [
                    'UC Berkeley campus family attractions',
                    'Berkeley Marina activities',
                    'Telegraph Avenue family',
                    'Fourth Street Berkeley shopping',
                    'Berkeley Hills hiking trails'
                ]
            },
            'San Francisco': {
                'coordinates': {'lat': 37.7749, 'lng': -122.4194},
                'radius': 15000,  # 15km radius - larger city
                'specific_searches': [
                    'Golden Gate Park family activities',
                    'Fisherman\'s Wharf kids attractions',
                    'Union Square family shopping',
                    'Mission District family restaurants',
                    'Chinatown San Francisco family'
                ]
            },
            'Oakland': {
                'coordinates': {'lat': 37.8044, 'lng': -122.2712},
                'radius': 10000,
                'specific_searches': [
                    'Lake Merritt family activities',
                    'Oakland Zoo and surroundings',
                    'Jack London Square family',
                    'Redwood Regional Park Oakland',
                    'Oakland Museum family programs'
                ]
            },
            'San Jose': {
                'coordinates': {'lat': 37.3382, 'lng': -121.8863},
                'radius': 12000,
                'specific_searches': [
                    'Santana Row family shopping',
                    'Winchester Mystery House family',
                    'San Jose tech museums',
                    'Guadalupe River Park trail',
                    'Willow Glen family dining'
                ]
            },
            'Palo Alto': {
                'coordinates': {'lat': 37.4419, 'lng': -122.1430},
                'radius': 6000,
                'specific_searches': [
                    'Stanford University family tours',
                    'Palo Alto Baylands nature center',
                    'University Avenue family dining',
                    'Mitchell Park family activities',
                    'Foothills Park hiking'
                ]
            }
        }
    
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def collect_all_cities_comprehensive(self):
        """Collect comprehensive data for all Bay Area cities"""
        
        if not self.api_key:
            return {"error": "No API key found"}
        
        # Universal activity categories that work for all cities
        universal_categories = [
            # Museums and Education
            "children museums {city}",
            "science museums {city}",
            "art galleries kids {city}",
            "libraries {city}",
            "aquariums {city}",
            
            # Parks and Outdoor
            "family parks {city}",
            "playgrounds {city}",
            "hiking trails easy {city}",
            "beaches near {city}",
            "botanical gardens {city}",
            
            # Recreation and Entertainment
            "bowling alleys family {city}",
            "movie theaters {city}",
            "ice skating {city}",
            "mini golf {city}",
            "trampoline parks {city}",
            "community centers {city}",
            "swimming pools public {city}",
            
            # Dining and Treats
            "family restaurants {city}",
            "ice cream shops {city}",
            "pizza family {city}",
            "bakeries kids {city}",
            
            # Shopping and Markets
            "farmers markets {city}",
            "toy stores {city}",
            "bookstores children {city}",
            
            # Classes and Learning
            "kids classes {city}",
            "art classes children {city}",
            "music classes kids {city}",
            "sports classes youth {city}"
        ]
        
        all_results = {}
        total_collected = 0
        
        for city_name, city_config in self.cities_config.items():
            print(f"\n🏙️ Starting comprehensive collection for {city_name}...")
            
            city_results = []
            city_count = 0
            
            # Search universal categories
            for category_template in universal_categories:
                search_query = category_template.format(city=city_name + " California")
                places = self.search_places_nearby(search_query, city_config)
                
                for place in places:
                    if self.is_in_city_area(place, city_name, city_config) and self.is_family_suitable(place):
                        enhanced_place = self.enhance_place_with_duration(place, city_name)
                        if enhanced_place and not self.is_duplicate(enhanced_place):
                            self.save_place_to_db(enhanced_place)
                            city_results.append(enhanced_place['name'])
                            city_count += 1
                            total_collected += 1
                
                time.sleep(1)  # Rate limiting
            
            # Search city-specific locations
            for specific_search in city_config.get('specific_searches', []):
                places = self.search_places_nearby(specific_search, city_config)
                
                for place in places:
                    if self.is_family_suitable(place):
                        enhanced_place = self.enhance_place_with_duration(place, city_name)
                        if enhanced_place and not self.is_duplicate(enhanced_place):
                            self.save_place_to_db(enhanced_place)
                            city_results.append(enhanced_place['name'])
                            city_count += 1
                            total_collected += 1
                
                time.sleep(1)
            
            all_results[city_name] = {
                'count': city_count,
                'sample_places': city_results[:5]  # First 5 as sample
            }
            
            print(f"✅ {city_name}: Found {city_count} places")
        
        return {
            "success": True,
            "message": f"Collected {total_collected} places across {len(self.cities_config)} cities",
            "cities": all_results,
            "total_collected": total_collected
        }
    
    def search_places_nearby(self, query, city_config):
        """Search places using nearby search for better results"""
        
        # Try text search first
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'key': self.api_key,
            'region': 'us',
            'language': 'en'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            return data.get('results', [])[:8]  # Limit results
        
        # Fallback to nearby search if text search fails
        nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        coords = city_config['coordinates']
        
        nearby_params = {
            'location': f"{coords['lat']},{coords['lng']}",
            'radius': city_config['radius'],
            'keyword': query.split()[-2] if len(query.split()) > 1 else query,  # Extract main keyword
            'key': self.api_key
        }
        
        nearby_response = requests.get(nearby_url, params=nearby_params)
        nearby_data = nearby_response.json()
        
        if nearby_data['status'] == 'OK':
            return nearby_data.get('results', [])[:8]
        
        return []
    
    def is_in_city_area(self, place, target_city, city_config):
        """Check if place is in the target city area"""
        address = place.get('formatted_address', '').lower()
        name = place.get('name', '').lower()
        
        # Check address contains city name
        if target_city.lower() in address:
            return True
        
        # Check coordinates are within reasonable distance
        geometry = place.get('geometry', {})
        location = geometry.get('location', {})
        place_lat = location.get('lat', 0)
        place_lng = location.get('lng', 0)
        
        if place_lat and place_lng:
            city_coords = city_config['coordinates']
            # Simple distance check (rough approximation)
            lat_diff = abs(place_lat - city_coords['lat'])
            lng_diff = abs(place_lng - city_coords['lng'])
            
            # If within ~0.15 degrees (roughly 10-15 miles), consider it nearby
            if lat_diff < 0.15 and lng_diff < 0.15:
                return True
        
        return False
    
    def is_family_suitable(self, place):
        """Enhanced family suitability check"""
        name = place.get('name', '').lower()
        types = place.get('types', [])
        
        # Family-friendly keywords
        family_keywords = [
            'children', 'kids', 'family', 'playground', 'park', 'museum', 
            'library', 'aquarium', 'zoo', 'science', 'discovery', 'nature',
            'community', 'recreation', 'school', 'learning', 'educational',
            'theater', 'cinema', 'bowling', 'ice cream', 'pizza', 'bakery',
            'swimming', 'sports', 'trail', 'beach', 'garden'
        ]
        
        # Family-friendly place types
        family_types = [
            'museum', 'park', 'library', 'aquarium', 'zoo', 'amusement_park',
            'tourist_attraction', 'point_of_interest', 'establishment',
            'community_center', 'movie_theater', 'bowling_alley', 'restaurant',
            'food', 'store', 'school', 'campground'
        ]
        
        # Exclude adult-only places
        exclude_keywords = [
            'bar', 'pub', 'nightclub', 'casino', 'dispensary', 
            'adult', 'lounge', 'cocktail', 'wine bar', 'brewery'
        ]
        
        # Check exclusions first
        for exclude in exclude_keywords:
            if exclude in name:
                return False
        
        # Check for family indicators
        for keyword in family_keywords:
            if keyword in name:
                return True
        
        for place_type in types:
            if place_type in family_types:
                return True
        
        return False
    
    def enhance_place_with_duration(self, place, city_name):
        """Enhanced place data with smart duration logic"""
        try:
            name = place.get('name', 'Unknown Place')
            rating = place.get('rating', 4.0)
            user_ratings_total = place.get('user_ratings_total', 0)
            formatted_address = place.get('formatted_address', '')
            place_id = place.get('place_id', '')
            
            geometry = place.get('geometry', {})
            location = geometry.get('location', {})
            latitude = location.get('lat')
            longitude = location.get('lng')
            
            place_types = place.get('types', [])
            activity_type = self.determine_activity_type(place_types, name)
            
            # Smart duration estimation
            duration_info = self.calculate_smart_duration(place_types, name, activity_type)
            
            cost_info = self.estimate_cost(place_types, name)
            tags = self.generate_comprehensive_tags(place_types, name, activity_type, duration_info)
            description = self.generate_description(name, place_types, city_name)
            
            enhanced_place = {
                'name': name,
                'description': description,
                'activity_type': activity_type,
                'rating': min(rating, 5.0),
                'review_count': user_ratings_total,
                'address': formatted_address,
                'city': city_name,
                'latitude': latitude,
                'longitude': longitude,
                'place_id': place_id,
                'cost_category': cost_info['category'],
                'price_min': cost_info.get('min_price'),
                'price_max': cost_info.get('max_price'),
                'duration_minutes': duration_info['duration_minutes'],
                'duration_category': duration_info['duration_category'],
                'recommended_time_slots': duration_info['time_slots'],
                'tags': tags,
                'source': 'google_places_multi_city',
                'is_open_now': place.get('opening_hours', {}).get('open_now', True),
                'google_types': place_types,
                'popularity_score': min(user_ratings_total, 100)
            }
            
            return enhanced_place
            
        except Exception as e:
            print(f"Error enhancing place data: {e}")
            return None
    
    def calculate_smart_duration(self, place_types, name, activity_type):
        """Smart duration calculation based on activity type and characteristics"""
        name_lower = name.lower()
        
        # Duration mapping based on activity type and specific indicators
        duration_rules = {
            # Quick activities (30 min - 1 hour)
            'quick': {
                'duration_minutes': 45,
                'duration_category': '30-60 min',
                'time_slots': ['morning', 'afternoon', 'evening'],
                'indicators': ['ice cream', 'cafe', 'quick', 'snack', 'treat', 'bakery']
            },
            
            # Short activities (1-2 hours)
            'short': {
                'duration_minutes': 90,
                'duration_category': '1-2 hrs',
                'time_slots': ['morning', 'afternoon'],
                'indicators': ['bowling', 'movie', 'small museum', 'library', 'playground']
            },
            
            # Medium activities (2-4 hours)
            'medium': {
                'duration_minutes': 180,
                'duration_category': '2-4 hrs',
                'time_slots': ['morning', 'afternoon'],
                'indicators': ['museum', 'zoo', 'aquarium', 'park', 'trail', 'shopping', 'beach']
            },
            
            # Long activities (4+ hours)
            'long': {
                'duration_minutes': 300,
                'duration_category': '4+ hrs',
                'time_slots': ['morning'],
                'indicators': ['amusement park', 'large park', 'campus', 'hiking', 'all day']
            }
        }
        
        # Check for specific duration indicators in name
        for category, info in duration_rules.items():
            for indicator in info['indicators']:
                if indicator in name_lower:
                    return info
        
        # Check by place type
        if any(t in place_types for t in ['restaurant', 'food', 'meal_takeaway']):
            return duration_rules['quick']
        elif any(t in place_types for t in ['movie_theater', 'bowling_alley']):
            return duration_rules['short']
        elif any(t in place_types for t in ['museum', 'aquarium', 'zoo']):
            return duration_rules['medium']
        elif any(t in place_types for t in ['amusement_park', 'campground']):
            return duration_rules['long']
        elif any(t in place_types for t in ['park']):
            # Parks can vary - check size indicators
            if any(word in name_lower for word in ['regional', 'state', 'national', 'large']):
                return duration_rules['long']
            else:
                return duration_rules['medium']
        
        # Default based on activity type
        if activity_type == 'dining':
            return duration_rules['quick']
        elif activity_type == 'educational':
            return duration_rules['medium']
        elif activity_type == 'outdoor':
            return duration_rules['medium']
        else:
            return duration_rules['short']
    
    def determine_activity_type(self, place_types, name):
        """Determine activity type"""
        name_lower = name.lower()
        
        if any(t in place_types for t in ['museum', 'library', 'university', 'school']):
            return 'educational'
        elif any(t in place_types for t in ['park', 'campground']):
            return 'outdoor'
        elif any(t in place_types for t in ['restaurant', 'food', 'meal_takeaway']):
            return 'dining'
        elif any(t in place_types for t in ['amusement_park', 'bowling_alley', 'movie_theater']):
            return 'recreational'
        else:
            return 'recreational'
    
    def estimate_cost(self, place_types, name):
        """Estimate cost based on type and name"""
        name_lower = name.lower()
        
        # Free places
        if any(t in place_types for t in ['park', 'library']) or any(word in name_lower for word in ['park', 'library', 'free', 'trail']):
            return {'category': 'free', 'min_price': 0, 'max_price': 0}
        
        # Low cost
        elif any(word in name_lower for word in ['ice cream', 'cafe', 'fast food']):
            return {'category': 'low', 'min_price': 5, 'max_price': 15}
        
        # Medium cost
        elif any(t in place_types for t in ['museum', 'movie_theater', 'bowling_alley']):
            return {'category': 'medium', 'min_price': 15, 'max_price': 35}
        
        # High cost
        elif any(word in name_lower for word in ['amusement', 'theme park']):
            return {'category': 'high', 'min_price': 35, 'max_price': 80}
        
        else:
            return {'category': 'low', 'min_price': 5, 'max_price': 25}
    
    def generate_comprehensive_tags(self, place_types, name, activity_type, duration_info):
        """Generate comprehensive tags including duration-based ones"""
        tags = []
        name_lower = name.lower()
        
        # Duration-based tags
        duration_category = duration_info['duration_category']
        if '30-60 min' in duration_category:
            tags.extend(['quick_visit', 'short_activity'])
        elif '1-2 hrs' in duration_category:
            tags.extend(['short_visit', 'half_day'])
        elif '2-4 hrs' in duration_category:
            tags.extend(['longer_visit', 'half_day'])
        elif '4+' in duration_category:
            tags.extend(['full_day', 'all_day'])
        
        # Time slot tags
        time_slots = duration_info['time_slots']
        if 'morning' in time_slots:
            tags.append('morning_activity')
        if 'afternoon' in time_slots:
            tags.append('afternoon_activity')
        if 'evening' in time_slots:
            tags.append('evening_activity')
        
        # Activity type tags
        if activity_type == 'educational':
            tags.extend(['learning', 'educational', 'indoor'])
        elif activity_type == 'outdoor':
            tags.extend(['outdoor', 'nature', 'fresh_air'])
        elif activity_type == 'recreational':
            tags.extend(['fun', 'entertainment'])
        elif activity_type == 'dining':
            tags.extend(['food', 'treats', 'indoor'])
        
        # Weather-appropriate tags
        if any(t in place_types for t in ['museum', 'library', 'movie_theater', 'bowling_alley', 'restaurant']):
            tags.append('rainy_day')
        if any(t in place_types for t in ['park', 'beach', 'trail']):
            tags.extend(['sunny_day', 'good_weather'])
        
        # Age-appropriate tags
        if any(word in name_lower for word in ['children', 'kids', 'toddler']):
            tags.append('kid_focused')
        if 'playground' in name_lower:
            tags.extend(['playground', 'active_play'])
        
        # Always include
        tags.extend(['family_friendly'])
        
        return list(set(tags))
    
    def generate_description(self, name, place_types, city_name):
        """Generate engaging description"""
        activity_descriptions = {
            'museum': f"Discover fascinating exhibits and interactive displays at {name} in {city_name}.",
            'park': f"Enjoy outdoor fun and beautiful surroundings at {name} in {city_name}.",
            'restaurant': f"Family-friendly dining experience at {name} in {city_name}.",
            'library': f"Educational programs and activities at {name} in {city_name}."
        }
        
        for place_type in place_types:
            if place_type in activity_descriptions:
                return activity_descriptions[place_type]
        
        return f"Family-friendly destination at {name} in {city_name}. Perfect for creating memories together."
    
    def is_duplicate(self, place_data):
        """Check for duplicates"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM activities 
                WHERE title = ? OR (title LIKE ? AND title LIKE ?)
            ''', (place_data['name'], f"%{place_data['name'][:10]}%", f"%{place_data['city']}%"))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            return False
        finally:
            conn.close()
    
    def save_place_to_db(self, place_data):
        """Save enhanced place to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert activity with duration info
            cursor.execute('''
                INSERT OR REPLACE INTO activities 
                (title, description, activity_type, cost_category, price_min, price_max,
                 duration_minutes, rating, created_at, updated_at, is_active, popularity_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                place_data['name'],
                place_data['description'],
                place_data['activity_type'],
                place_data['cost_category'],
                place_data['price_min'],
                place_data['price_max'],
                place_data['duration_minutes'],
                place_data['rating'],
                datetime.now(),
                datetime.now(),
                place_data.get('popularity_score', 10)
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
                cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                tag_result = cursor.fetchone()
                
                if tag_result:
                    tag_id = tag_result[0]
                else:
                    cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = cursor.lastrowid
                
                cursor.execute('''
                    INSERT OR IGNORE INTO activity_tags (activity_id, tag_id)
                    VALUES (?, ?)
                ''', (activity_id, tag_id))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error saving place {place_data['name']}: {e}")
            conn.rollback()
        finally:
            conn.close()

# Main function
def run_multi_city_smart_collection():
    """Run the multi-city smart collection"""
    collector = MultiCitySmartCollector()
    result = collector.collect_all_cities_comprehensive()
    return result

if __name__ == "__main__":
    result = run_multi_city_smart_collection()
    print(json.dumps(result, indent=2))
