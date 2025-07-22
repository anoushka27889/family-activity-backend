# Enhanced Google Places API Collector for Rich Family Activity Data
# Collects venues with photos, reviews, hours, pricing, and real-time data

import requests
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)

class EnhancedGooglePlacesCollector:
    def __init__(self, api_key: str, db_path: str = 'activities.db'):
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.places_new_url = "https://places.googleapis.com/v1/places"
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def collect_rich_family_places(self, cities: List[str]):
        """Collect comprehensive family activity data from Google Places"""
        
        # Comprehensive family-friendly place types
        family_place_types = {
            'amusement_park': {'min_age': 3, 'max_age': 18, 'activity_type': 'recreational'},
            'aquarium': {'min_age': 2, 'max_age': 18, 'activity_type': 'educational'},
            'art_gallery': {'min_age': 5, 'max_age': 18, 'activity_type': 'educational'},
            'bowling_alley': {'min_age': 4, 'max_age': 18, 'activity_type': 'recreational'},
            'campground': {'min_age': 0, 'max_age': 18, 'activity_type': 'outdoor'},
            'library': {'min_age': 0, 'max_age': 18, 'activity_type': 'educational'},
            'museum': {'min_age': 3, 'max_age': 18, 'activity_type': 'educational'},
            'park': {'min_age': 0, 'max_age': 18, 'activity_type': 'outdoor'},
            'tourist_attraction': {'min_age': 2, 'max_age': 18, 'activity_type': 'recreational'},
            'zoo': {'min_age': 1, 'max_age': 18, 'activity_type': 'educational'}
        }
        
        # Specific family keywords for text search
        family_keywords = [
            'children playground',
            'kids activities',
            'family fun center',
            'children museum',
            'indoor playground',
            'trampoline park',
            'mini golf',
            'kids gym',
            'story time',
            'children library programs',
            'family swimming',
            'kids art classes',
            'children theater',
            'family hiking trails',
            'kids birthday parties'
        ]
        
        for city in cities:
            logger.info(f"Collecting data for {city}...")
            
            # Search by place types
            for place_type, age_info in family_place_types.items():
                self.search_places_by_type(city, place_type, age_info)
                time.sleep(1)  # Rate limiting
            
            # Search by family keywords
            for keyword in family_keywords:
                self.search_places_by_text(city, keyword)
                time.sleep(1)  # Rate limiting
    
    def search_places_by_type(self, city: str, place_type: str, age_info: Dict):
        """Search for places by type with comprehensive data"""
        url = f"{self.base_url}/nearbysearch/json"
        
        # Get city coordinates first
        city_coords = self.get_city_coordinates(city)
        if not city_coords:
            return
        
        params = {
            'location': f"{city_coords['lat']},{city_coords['lng']}",
            'radius': 25000,  # 25km radius
            'type': place_type,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                for place in data.get('results', []):
                    # Get detailed place information
                    detailed_place = self.get_place_details(place['place_id'])
                    if detailed_place:
                        self.process_enhanced_place(detailed_place, city, age_info)
            
            # Handle pagination
            while 'next_page_token' in data:
                time.sleep(2)  # Required delay for next_page_token
                params['pagetoken'] = data['next_page_token']
                response = requests.get(url, params=params)
                data = response.json()
                
                if data['status'] == 'OK':
                    for place in data.get('results', []):
                        detailed_place = self.get_place_details(place['place_id'])
                        if detailed_place:
                            self.process_enhanced_place(detailed_place, city, age_info)
                            
        except Exception as e:
            logger.error(f"Error searching {place_type} in {city}: {e}")
    
    def search_places_by_text(self, city: str, keyword: str):
        """Search for places using text search for specific family activities"""
        url = f"{self.base_url}/textsearch/json"
        
        params = {
            'query': f"{keyword} in {city}",
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                for place in data.get('results', []):
                    detailed_place = self.get_place_details(place['place_id'])
                    if detailed_place:
                        # Determine age info from keyword
                        age_info = self.determine_age_from_keyword(keyword)
                        self.process_enhanced_place(detailed_place, city, age_info)
                        
        except Exception as e:
            logger.error(f"Error searching '{keyword}' in {city}: {e}")
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get comprehensive place details including photos, reviews, hours, etc."""
        url = f"{self.base_url}/details/json"
        
        # Request all available fields for rich data
        fields = [
            'place_id', 'name', 'formatted_address', 'geometry', 'photos',
            'rating', 'user_ratings_total', 'reviews', 'opening_hours',
            'phone_number', 'website', 'price_level', 'types',
            'business_status', 'current_opening_hours', 'editorial_summary',
            'vicinity', 'url', 'utc_offset', 'wheelchair_accessible_entrance'
        ]
        
        params = {
            'place_id': place_id,
            'fields': ','.join(fields),
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                return data['result']
            else:
                logger.warning(f"Failed to get details for {place_id}: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return None
    
    def process_enhanced_place(self, place: Dict, city: str, age_info: Dict):
        """Process place with all rich data including photos, reviews, hours"""
        try:
            # Extract basic information
            place_id = place.get('place_id')
            name = place.get('name', 'Unknown Place')
            description = self.generate_rich_description(place)
            
            # Extract location data
            geometry = place.get('geometry', {}).get('location', {})
            latitude = geometry.get('lat')
            longitude = geometry.get('lng')
            address = place.get('formatted_address', '')
            
            # Extract rating and reviews
            rating = place.get('rating', 0)
            review_count = place.get('user_ratings_total', 0)
            reviews = place.get('reviews', [])
            
            # Extract photos
            photos = self.extract_photo_urls(place.get('photos', []))
            
            # Extract hours and current status
            hours_info = self.process_opening_hours(place.get('current_opening_hours', {}))
            
            # Extract pricing information
            price_info = self.determine_pricing(place.get('price_level'), place.get('types', []))
            
            # Generate comprehensive tags
            tags = self.generate_comprehensive_tags(place, age_info)
            
            # Check if place is currently open
            is_open_now = place.get('current_opening_hours', {}).get('open_now', False)
            
            # Extract accessibility info
            is_accessible = place.get('wheelchair_accessible_entrance', False)
            
            # Save to database with all rich data
            activity_data = {
                'title': name,
                'description': description,
                'activity_type': age_info.get('activity_type', 'recreational'),
                'min_age': age_info.get('min_age', 0),
                'max_age': age_info.get('max_age', 18),
                'cost_category': price_info['category'],
                'price_min': price_info.get('min_price'),
                'price_max': price_info.get('max_price'),
                'venue_name': name,
                'address': address,
                'city': city,
                'latitude': latitude,
                'longitude': longitude,
                'rating': rating,
                'review_count': review_count,
                'phone': place.get('phone_number'),
                'website': place.get('website'),
                'google_url': place.get('url'),
                'place_id': place_id,
                'photos': photos,
                'hours': hours_info,
                'is_open_now': is_open_now,
                'is_accessible': is_accessible,
                'business_status': place.get('business_status'),
                'tags': tags,
                'google_reviews': reviews[:3],  # Store top 3 reviews
                'last_updated': datetime.now()
            }
            
            activity_id = self.save_enhanced_activity(activity_data)
            
            # Save reviews separately
            for review in reviews[:5]:  # Save top 5 reviews
                self.save_google_review(activity_id, review)
            
            logger.info(f"Saved enhanced place: {name} (Rating: {rating}, Reviews: {review_count})")
            
        except Exception as e:
            logger.error(f"Error processing place {place.get('name', 'Unknown')}: {e}")
    
    def save_enhanced_activity(self, activity_data: Dict) -> int:
        """Save activity with all enhanced data"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert/update main activity
            cursor.execute('''
                INSERT OR REPLACE INTO activities 
                (title, description, activity_type, min_age, max_age, 
                 cost_category, price_min, price_max, rating, 
                 created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                activity_data['title'], activity_data['description'], 
                activity_data['activity_type'], activity_data['min_age'], 
                activity_data['max_age'], activity_data['cost_category'],
                activity_data['price_min'], activity_data['price_max'],
                activity_data['rating'], datetime.now(), datetime.now()
            ))
            
            activity_id = cursor.lastrowid
            
            # Insert/update venue with rich data
            cursor.execute('''
                INSERT OR REPLACE INTO venues 
                (name, address, city, latitude, longitude, rating, 
                 phone, website, google_place_id, google_url,
                 is_wheelchair_accessible, business_status, 
                 venue_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_data['venue_name'], activity_data['address'],
                activity_data['city'], activity_data['latitude'],
                activity_data['longitude'], activity_data['rating'],
                activity_data.get('phone'), activity_data.get('website'),
                activity_data['place_id'], activity_data.get('google_url'),
                activity_data['is_accessible'], activity_data.get('business_status'),
                activity_data['activity_type'], datetime.now(), datetime.now()
            ))
            
            venue_id = cursor.lastrowid
            
            # Link activity to venue
            cursor.execute('''
                INSERT OR IGNORE INTO activity_venues (activity_id, venue_id)
                VALUES (?, ?)
            ''', (activity_id, venue_id))
            
            # Save photos
            for photo_url in activity_data.get('photos', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO activity_photos 
                    (activity_id, photo_url, uploaded_by, moderation_status)
                    VALUES (?, ?, 'google_places', 'approved')
                ''', (activity_id, photo_url))
            
            # Save tags
            for tag in activity_data.get('tags', []):
                # Get or create tag
                cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,))
                tag_result = cursor.fetchone()
                
                if tag_result:
                    tag_id = tag_result[0]
                else:
                    cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag,))
                    tag_id = cursor.lastrowid
                
                # Link activity to tag
                cursor.execute('''
                    INSERT OR IGNORE INTO activity_tags (activity_id, tag_id)
                    VALUES (?, ?)
                ''', (activity_id, tag_id))
            
            # Save hours information
            if activity_data.get('hours'):
                cursor.execute('''
                    UPDATE venues SET 
                    opening_hours = ?,
                    is_open_now = ?
                    WHERE id = ?
                ''', (
                    json.dumps(activity_data['hours']),
                    activity_data['is_open_now'],
                    venue_id
                ))
            
            conn.commit()
            return activity_id
            
        except Exception as e:
            logger.error(f"Error saving enhanced activity: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def save_google_review(self, activity_id: int, review: Dict):
        """Save Google review data"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO activity_reviews 
                (activity_id, user_name, rating, review_text, 
                 created_at, helpful_votes, verified_visit)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (
                activity_id,
                review.get('author_name', 'Google User'),
                review.get('rating', 5),
                review.get('text', '')[:500],  # Limit length
                datetime.now(),
                0  # Google reviews don't have helpful votes
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving review: {e}")
        finally:
            conn.close()
    
    # Helper methods
    def get_city_coordinates(self, city: str) -> Optional[Dict]:
        """Get coordinates for a city"""
        city_coords = {
            'Berkeley': {'lat': 37.8715, 'lng': -122.2730},
            'San Francisco': {'lat': 37.7749, 'lng': -122.4194},
            'Oakland': {'lat': 37.8044, 'lng': -122.2712},
            'San Jose': {'lat': 37.3382, 'lng': -121.8863},
            'Sausalito': {'lat': 37.8590, 'lng': -122.4852}
        }
        return city_coords.get(city)
    
    def extract_photo_urls(self, photos: List[Dict]) -> List[str]:
        """Extract high-quality photo URLs from Google Places photos"""
        photo_urls = []
        
        for photo in photos[:5]:  # Limit to 5 photos
            photo_reference = photo.get('photo_reference')
            if photo_reference:
                # Generate high-quality photo URL
                photo_url = f"{self.base_url}/photo?maxwidth=800&photoreference={photo_reference}&key={self.api_key}"
                photo_urls.append(photo_url)
        
        return photo_urls
    
    def generate_rich_description(self, place: Dict) -> str:
        """Generate rich description from place data"""
        name = place.get('name', '')
        editorial_summary = place.get('editorial_summary', {}).get('overview', '')
        types = place.get('types', [])
        rating = place.get('rating', 0)
        review_count = place.get('user_ratings_total', 0)
        
        # Create engaging description
        description_parts = []
        
        if editorial_summary:
            description_parts.append(editorial_summary)
        else:
            # Generate description based on type
            type_descriptions = {
                'amusement_park': 'Fun-filled amusement park with rides and attractions for the whole family.',
                'aquarium': 'Explore marine life and underwater worlds in this family-friendly aquarium.',
                'museum': 'Educational and engaging museum experience perfect for curious minds.',
                'park': 'Beautiful outdoor space perfect for family activities and recreation.',
                'zoo': 'Meet amazing animals from around the world in this family-friendly zoo.',
                'library': 'Community hub offering books, programs, and activities for all ages.'
            }
            
            for place_type in types:
                if place_type in type_descriptions:
                    description_parts.append(type_descriptions[place_type])
                    break
        
        # Add rating information
        if rating > 0 and review_count > 0:
            description_parts.append(f"Highly rated by families with {rating}/5 stars from {review_count} reviews.")
        
        return ' '.join(description_parts) or f"Family-friendly destination at {name}."
    
    def process_opening_hours(self, hours_data: Dict) -> Dict:
        """Process opening hours into structured format"""
        if not hours_data:
            return {}
        
        return {
            'weekday_text': hours_data.get('weekday_text', []),
            'open_now': hours_data.get('open_now', False),
            'periods': hours_data.get('periods', [])
        }
    
    def determine_pricing(self, price_level: Optional[int], types: List[str]) -> Dict:
        """Determine pricing information"""
        if price_level is None:
            # Estimate based on place type
            free_types = ['park', 'library', 'playground']
            if any(t in types for t in free_types):
                return {'category': 'free', 'min_price': 0, 'max_price': 0}
            else:
                return {'category': 'unknown'}
        
        price_mapping = {
            0: {'category': 'free', 'min_price': 0, 'max_price': 0},
            1: {'category': 'low', 'min_price': 5, 'max_price': 15},
            2: {'category': 'medium', 'min_price': 15, 'max_price': 30},
            3: {'category': 'high', 'min_price': 30, 'max_price': 60},
            4: {'category': 'very_high', 'min_price': 60, 'max_price': 100}
        }
        
        return price_mapping.get(price_level, {'category': 'unknown'})
    
    def generate_comprehensive_tags(self, place: Dict, age_info: Dict) -> List[str]:
        """Generate comprehensive tags from place data"""
        tags = []
        
        # Add activity type
        tags.append(age_info.get('activity_type', 'recreational'))
        
        # Add place type tags
        place_types = place.get('types', [])
        type_tag_mapping = {
            'amusement_park': ['fun', 'rides', 'exciting'],
            'aquarium': ['marine_life', 'educational', 'animals'],
            'art_gallery': ['art', 'culture', 'creative'],
            'bowling_alley': ['sports', 'indoor', 'social'],
            'library': ['reading', 'educational', 'quiet', 'free'],
            'museum': ['educational', 'interactive', 'learning'],
            'park': ['outdoor', 'nature', 'playground', 'free'],
            'zoo': ['animals', 'educational', 'outdoor']
        }
        
        for place_type in place_types:
            if place_type in type_tag_mapping:
                tags.extend(type_tag_mapping[place_type])
        
        # Add age-appropriate tags
        min_age = age_info.get('min_age', 0)
        max_age = age_info.get('max_age', 18)
        
        if min_age <= 2:
            tags.append('toddler_friendly')
        if min_age <= 5:
            tags.append('preschool_friendly')
        if max_age >= 12:
            tags.append('school_age_friendly')
        if max_age >= 16:
            tags.append('teen_friendly')
        
        # Add accessibility tags
        if place.get('wheelchair_accessible_entrance'):
            tags.append('wheelchair_accessible')
        
        # Add rating-based tags
        rating = place.get('rating', 0)
        if rating >= 4.5:
            tags.append('highly_rated')
        if place.get('user_ratings_total', 0) > 100:
            tags.append('popular')
        
        # Add operational tags
        if place.get('current_opening_hours', {}).get('open_now'):
            tags.append('open_now')
        
        return list(set(tags))  # Remove duplicates
    
    def determine_age_from_keyword(self, keyword: str) -> Dict:
        """Determine age range from search keyword"""
        keyword_lower = keyword.lower()
        
        if 'toddler' in keyword_lower or 'baby' in keyword_lower:
            return {'activity_type': 'educational', 'min_age': 0, 'max_age': 3}
        elif 'children' in keyword_lower or 'kids' in keyword_lower:
            return {'activity_type': 'recreational', 'min_age': 3, 'max_age': 12}
        elif 'family' in keyword_lower:
            return {'activity_type': 'recreational', 'min_age': 0, 'max_age': 18}
        else:
            return {'activity_type': 'recreational', 'min_age': 3, 'max_age': 12}

# Usage function
def run_google_places_collection():
    """Run the Google Places enhanced collection"""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY environment variable not set")
        return
    
    collector = EnhancedGooglePlacesCollector(api_key)
    
    # Cities to collect data for
    cities = ['Berkeley', 'San Francisco', 'Oakland', 'San Jose', 'Sausalito']
    
    print("Starting enhanced Google Places data collection...")
    collector.collect_rich_family_places(cities)
    print("Collection completed!")

if __name__ == "__main__":
    run_google_places_collection()
