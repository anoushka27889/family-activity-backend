# Clean Backend - No Fake Data, Real API Ready
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
import requests
import random
import time

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_PATH = 'activities.db'

# API Keys - Add real keys in Render environment variables
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            activity_type TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 120,
            cost_category TEXT DEFAULT 'unknown',
            price_min DECIMAL(10,2),
            price_max DECIMAL(10,2),
            rating REAL DEFAULT 4.0,
            review_count INTEGER DEFAULT 0,
            venue_name TEXT,
            address TEXT,
            city TEXT NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            phone TEXT,
            website TEXT,
            is_open_now BOOLEAN DEFAULT 1,
            google_place_id TEXT,
            source TEXT DEFAULT 'manual',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def collect_google_places_data(location, search_query):
    """Collect REAL data from Google Places API"""
    if not GOOGLE_PLACES_API_KEY:
        return []
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f'{search_query} {location}',
            'key': GOOGLE_PLACES_API_KEY,
            'region': 'us',
            'language': 'en'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'OK':
            real_activities = []
            for place in data.get('results', [])[:5]:
                if is_family_suitable(place):
                    real_activities.append({
                        'title': place.get('name'),
                        'description': place.get('formatted_address', ''),
                        'activity_type': determine_activity_type(place.get('types', [])),
                        'duration_minutes': estimate_duration(place.get('types', [])),
                        'cost_category': estimate_cost(place.get('types', []), place.get('name', '')),
                        'rating': place.get('rating', 4.0),
                        'review_count': place.get('user_ratings_total', 0),
                        'venue_name': place.get('name'),
                        'address': place.get('formatted_address', ''),
                        'city': location,
                        'latitude': place.get('geometry', {}).get('location', {}).get('lat'),
                        'longitude': place.get('geometry', {}).get('location', {}).get('lng'),
                        'is_open_now': place.get('opening_hours', {}).get('open_now', True),
                        'google_place_id': place.get('place_id'),
                        'source': 'google_places'
                    })
            return real_activities
        else:
            print(f"Google Places API error: {data.get('status')}")
            return []
            
    except Exception as e:
        print(f"Error collecting Google Places data: {e}")
        return []

def is_family_suitable(place):
    """Check if place is suitable for families"""
    name = place.get('name', '').lower()
    types = place.get('types', [])
    
    # Family-friendly keywords
    family_keywords = ['children', 'kids', 'family', 'playground', 'park', 'museum', 'library']
    exclude_keywords = ['bar', 'pub', 'nightclub', 'casino', 'adult']
    
    # Check exclusions
    for exclude in exclude_keywords:
        if exclude in name:
            return False
    
    # Check family indicators
    for keyword in family_keywords:
        if keyword in name:
            return True
    
    # Family-friendly place types
    family_types = ['museum', 'park', 'library', 'tourist_attraction', 'establishment']
    for place_type in types:
        if place_type in family_types:
            return True
    
    return place.get('rating', 0) >= 4.0

def determine_activity_type(place_types):
    """Determine activity type from Google place types"""
    if any(t in place_types for t in ['park', 'campground']):
        return 'outdoor'
    elif any(t in place_types for t in ['museum', 'library', 'university']):
        return 'educational'
    elif any(t in place_types for t in ['restaurant', 'food']):
        return 'dining'
    else:
        return 'recreational'

def estimate_duration(place_types):
    """Estimate duration based on place type"""
    duration_map = {
        'museum': 180,
        'park': 120,
        'library': 60,
        'restaurant': 90,
        'amusement_park': 300
    }
    
    for place_type in place_types:
        if place_type in duration_map:
            return duration_map[place_type]
    return 120

def estimate_cost(place_types, name):
    """Estimate cost based on place type"""
    name_lower = name.lower()
    
    if any(t in place_types for t in ['park', 'library']) or 'free' in name_lower:
        return 'free'
    elif any(t in place_types for t in ['museum']):
        return 'medium'
    else:
        return 'low'

def format_duration(duration_minutes):
    """Format duration for display"""
    if not duration_minutes:
        return "2-3 hrs"
    
    if duration_minutes <= 45:
        return "30-45 min"
    elif duration_minutes <= 90:
        return "1-1.5 hrs"
    elif duration_minutes <= 180:
        return "2-3 hrs"
    elif duration_minutes <= 300:
        return "4-5 hrs"
    else:
        return "All day"

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """Get activities - real data only"""
    try:
        location = request.args.get('location', 'Berkeley')
        duration = request.args.get('duration', '')
        filters = request.args.getlist('filters[]')
        mood_hint = request.args.get('mood_hint', '')
        
        # If no Google Places API key, return helpful message
        if not GOOGLE_PLACES_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Google Places API key not configured',
                'message': 'Please add GOOGLE_PLACES_API_KEY to environment variables to get real activity data'
            })
        
        # Determine search query based on filters and mood
        search_queries = []
        
        if mood_hint:
            mood_lower = mood_hint.lower()
            if 'antsy' in mood_lower or 'energy' in mood_lower:
                search_queries = ['family parks', 'playgrounds', 'outdoor activities kids']
            elif 'calm' in mood_lower or 'quiet' in mood_lower:
                search_queries = ['libraries', 'quiet museums', 'reading centers']
            elif 'creative' in mood_lower:
                search_queries = ['art classes kids', 'craft centers', 'creative workshops']
            else:
                search_queries = ['family activities', 'kids attractions']
        else:
            # Default searches based on filters
            if 'OUTDOOR' in filters:
                search_queries = ['family parks', 'playgrounds', 'outdoor activities']
            elif 'INDOOR' in filters:
                search_queries = ['children museums', 'libraries', 'indoor activities']
            elif 'FREE' in filters:
                search_queries = ['free family activities', 'free parks', 'free libraries']
            else:
                search_queries = ['family activities', 'kids attractions', 'children museums']
        
        # Collect real data from Google Places
        all_activities = []
        for query in search_queries[:2]:  # Limit to 2 searches to avoid quota
            real_activities = collect_google_places_data(location, query)
            all_activities.extend(real_activities)
            time.sleep(1)  # Rate limiting
        
        # Save real activities to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        saved_activities = []
        for activity in all_activities:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO activities 
                    (title, description, activity_type, duration_minutes, cost_category,
                     rating, review_count, venue_name, address, city, latitude, longitude,
                     is_open_now, google_place_id, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity['title'], activity['description'], activity['activity_type'],
                    activity['duration_minutes'], activity['cost_category'], activity['rating'],
                    activity['review_count'], activity['venue_name'], activity['address'],
                    activity['city'], activity['latitude'], activity['longitude'],
                    activity['is_open_now'], activity['google_place_id'], activity['source'],
                    datetime.now(), datetime.now()
                ))
                
                # Format for response
                formatted_activity = {
                    'id': str(cursor.lastrowid),
                    'title': activity['title'],
                    'description': activity['description'],
                    'activity_type': activity['activity_type'],
                    'duration': format_duration(activity['duration_minutes']),
                    'duration_minutes': activity['duration_minutes'],
                    'cost_category': activity['cost_category'],
                    'venue_name': activity['venue_name'],
                    'address': activity['address'],
                    'city': activity['city'],
                    'rating': activity['rating'],
                    'review_count': activity['review_count'],
                    'is_open_now': activity['is_open_now'],
                    'source': activity['source']
                }
                saved_activities.append(formatted_activity)
                
            except Exception as e:
                print(f"Error saving activity: {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': saved_activities,
            'count': len(saved_activities),
            'message': f'Found {len(saved_activities)} real activities in {location}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/activities/mood-search', methods=['POST'])
def mood_search():
    """Mood-based search using real Google Places data"""
    try:
        data = request.json
        query = data.get('query', '')
        location = data.get('location', 'Berkeley')
        
        if not GOOGLE_PLACES_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Google Places API key not configured'
            })
        
        # Convert mood to search query
        mood_lower = query.lower()
        if 'antsy' in mood_lower or 'energy' in mood_lower or 'bouncing' in mood_lower:
            search_query = 'playgrounds parks outdoor activities kids'
        elif 'calm' in mood_lower or 'quiet' in mood_lower:
            search_query = 'libraries quiet museums reading'
        elif 'creative' in mood_lower or 'art' in mood_lower:
            search_query = 'art museums creative centers kids'
        elif 'curious' in mood_lower or 'learn' in mood_lower:
            search_query = 'science museums educational centers'
        else:
            search_query = 'family activities kids attractions'
        
        # Get real data
        real_activities = collect_google_places_data(location, search_query)
        
        # Format for response
        formatted_activities = []
        for activity in real_activities:
            formatted_activities.append({
                'id': activity.get('google_place_id', str(random.randint(1000, 9999))),
                'title': activity['title'],
                'description': activity['description'],
                'activity_type': activity['activity_type'],
                'duration': format_duration(activity['duration_minutes']),
                'cost_category': activity['cost_category'],
                'venue_name': activity['venue_name'],
                'address': activity['address'],
                'city': activity['city'],
                'rating': activity['rating'],
                'is_open_now': activity['is_open_now'],
                'source': activity['source']
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'activities': formatted_activities,
            'count': len(formatted_activities)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'TOT TROT API is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0 - Real Data Only',
        'google_places_configured': bool(GOOGLE_PLACES_API_KEY),
        'features': [
            'Real Google Places integration',
            'Live venue data',
            'Mood-based search'
        ]
    })

@app.route('/api/collect-data', methods=['POST'])
def collect_fresh_data():
    """Manually collect fresh real data"""
    try:
        location = request.json.get('location', 'Berkeley')
        
        if not GOOGLE_PLACES_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Google Places API key required'
            })
        
        # Collect from multiple categories
        search_categories = [
            'family parks',
            'children museums',
            'libraries',
            'playgrounds',
            'kids activities'
        ]
        
        all_collected = []
        for category in search_categories:
            activities = collect_google_places_data(location, category)
            all_collected.extend(activities)
            time.sleep(1)  # Rate limiting
        
        return jsonify({
            'success': True,
            'message': f'Collected {len(all_collected)} real activities for {location}',
            'count': len(all_collected)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting TOT TROT API - Real Data Only")
    print("🔑 Google Places API:", "✅ Configured" if GOOGLE_PLACES_API_KEY else "❌ Missing")
    
    create_tables()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
