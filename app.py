# Enhanced Backend API Server for Family Activity App
# Building on your original Flask backend with AI enhancements

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
CORS(app)  # Allow requests from your React app

# Database configuration
DATABASE_PATH = 'activities.db'

# API Keys - Add these to your environment variables in Render
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'your_google_places_key_here')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your_openai_key_here')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def create_tables():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enhanced activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            ai_enhanced_description TEXT,
            activity_type TEXT NOT NULL,
            min_age INTEGER,
            max_age INTEGER,
            duration_minutes INTEGER DEFAULT 120,
            cost_category TEXT DEFAULT 'unknown',
            price_min DECIMAL(10,2),
            price_max DECIMAL(10,2),
            rating REAL DEFAULT 4.0,
            review_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            
            -- AI Enhancement Fields (the magic!)
            joy_factors TEXT, -- JSON array of joy factors
            parent_whisper TEXT, -- Insider tip from parents
            surprise_element TEXT, -- Hidden delight
            mood_tags TEXT, -- JSON array of mood tags
            spontaneity_score REAL DEFAULT 0.8 -- How good for "right now"
        )
    ''')
    
    # Enhanced venues table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            venue_type TEXT NOT NULL,
            address TEXT,
            city TEXT NOT NULL,
            state TEXT DEFAULT 'CA',
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            phone TEXT,
            website TEXT,
            rating DECIMAL(3,2),
            is_open_now BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            venue_id INTEGER NOT NULL,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
            FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
            UNIQUE(activity_id, venue_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully!")

def create_ai_enhanced_activity(name, description, activity_type, city, **kwargs):
    """Create an AI-enhanced activity with joy factors and parent tips"""
    
    # AI Enhancement (simplified version - can be replaced with real OpenAI calls)
    joy_factors = []
    parent_whisper = ""
    surprise_element = ""
    mood_tags = []
    spontaneity_score = 0.8
    
    # Simple rule-based enhancement (replace with OpenAI API call)
    if 'park' in name.lower() or activity_type == 'outdoor':
        joy_factors = [
            "Kids love running free in open space",
            "Perfect for burning energy and being loud", 
            "Great for impromptu games and exploration"
        ]
        parent_whisper = "Check for hidden play areas behind the main playground"
        surprise_element = "Look for the secret climbing tree most kids don't notice"
        mood_tags = ["antsy", "energetic", "outdoor"]
        spontaneity_score = 0.9
        
    elif 'museum' in name.lower() or activity_type == 'educational':
        joy_factors = [
            "Interactive exhibits capture curious minds",
            "Learning feels like playing and discovering",
            "Perfect for kids who ask 'why' about everything"
        ]
        parent_whisper = "Visit right when they open for smaller crowds and excited staff"
        surprise_element = "Ask at the front desk about hands-on demonstrations"
        mood_tags = ["curious", "calm", "educational"]
        spontaneity_score = 0.7
        
    elif 'library' in name.lower():
        joy_factors = [
            "Cozy reading nooks feel like secret hideouts",
            "Story time brings books to life with voices and songs",
            "Kids love the treasure hunt feeling of finding new books"
        ]
        parent_whisper = "Librarians often have stickers and know the best new books"
        surprise_element = "Many libraries have puzzles and games you can borrow"
        mood_tags = ["calm", "curious", "quiet"]
        spontaneity_score = 0.8
        
    else:
        joy_factors = [
            "Great place for family bonding and making memories",
            "Kids usually discover something new every visit",
            "Perfect for when you want to try something different"
        ]
        parent_whisper = "Call ahead to check current hours and availability"
        surprise_element = "Every family finds their own favorite spot here"
        mood_tags = ["social", "fun"]
        spontaneity_score = 0.6
    
    return {
        'title': name,
        'description': description,
        'ai_enhanced_description': f"Family-friendly {name} in {city} - {description}",
        'activity_type': activity_type,
        'city': city,
        'joy_factors': json.dumps(joy_factors),
        'parent_whisper': parent_whisper,
        'surprise_element': surprise_element,
        'mood_tags': json.dumps(mood_tags),
        'spontaneity_score': spontaneity_score,
        **kwargs
    }

def init_database_with_sample_data():
    """Initialize database with sample AI-enhanced data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we have any activities
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Initializing database with AI-enhanced sample data...")
        
        # Sample AI-enhanced activities
        sample_activities = [
            create_ai_enhanced_activity(
                name="Tilden Nature Area",
                description="Beautiful hiking trails, playground, and nature center with easy walks for families.",
                activity_type="outdoor",
                city="Berkeley",
                duration_minutes=240,
                cost_category="free",
                rating=4.8
            ),
            create_ai_enhanced_activity(
                name="California Academy of Sciences",
                description="Natural history museum with aquarium, planetarium, and rainforest dome.",
                activity_type="educational",
                city="San Francisco",
                duration_minutes=300,
                cost_category="high",
                price_min=40,
                price_max=45,
                rating=4.7
            ),
            create_ai_enhanced_activity(
                name="Berkeley Public Library Story Time",
                description="Weekly interactive story sessions with songs and activities for young children.",
                activity_type="educational",
                city="Berkeley",
                duration_minutes=45,
                cost_category="free",
                rating=4.3
            ),
            create_ai_enhanced_activity(
                name="Golden Gate Park Playground",
                description="Large playground with climbing structures, swings, and open space for running.",
                activity_type="outdoor",
                city="San Francisco",
                duration_minutes=120,
                cost_category="free",
                rating=4.4
            ),
            create_ai_enhanced_activity(
                name="Oakland Zoo",
                description="Home to over 700 native and exotic animals with interactive experiences.",
                activity_type="educational",
                city="Oakland",
                duration_minutes=240,
                cost_category="medium",
                price_min=20,
                price_max=25,
                rating=4.3
            ),
            create_ai_enhanced_activity(
                name="Chabot Space & Science Center",
                description="Interactive science museum with planetarium and hands-on exhibits about space and science.",
                activity_type="educational",
                city="Oakland",
                duration_minutes=180,
                cost_category="medium",
                price_min=18,
                price_max=22,
                rating=4.5
            ),
            create_ai_enhanced_activity(
                name="Crissy Field",
                description="Open waterfront park with Golden Gate Bridge views, perfect for picnics and kite flying.",
                activity_type="outdoor",
                city="San Francisco",
                duration_minutes=150,
                cost_category="free",
                rating=4.6
            ),
            create_ai_enhanced_activity(
                name="Children's Creativity Museum",
                description="Hands-on multimedia museum where kids can create stop-motion videos and music videos.",
                activity_type="educational",
                city="San Francisco",
                duration_minutes=120,
                cost_category="medium",
                price_min=12,
                price_max=15,
                rating=4.4
            )
        ]
        
        # Insert activities
        for activity in sample_activities:
            cursor.execute('''
                INSERT INTO activities 
                (title, description, ai_enhanced_description, activity_type, 
                 duration_minutes, cost_category, price_min, price_max, rating,
                 joy_factors, parent_whisper, surprise_element, mood_tags, spontaneity_score,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['title'], activity['description'], activity['ai_enhanced_description'],
                activity['activity_type'], activity['duration_minutes'], activity['cost_category'],
                activity.get('price_min'), activity.get('price_max'), activity['rating'],
                activity['joy_factors'], activity['parent_whisper'], activity['surprise_element'],
                activity['mood_tags'], activity['spontaneity_score'],
                datetime.now(), datetime.now()
            ))
            
            activity_id = cursor.lastrowid
            
            # Insert venue
            cursor.execute('''
                INSERT INTO venues 
                (name, address, city, rating, venue_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['title'], activity['description'], activity['city'],
                activity['rating'], activity['activity_type'], datetime.now(), datetime.now()
            ))
            
            venue_id = cursor.lastrowid
            
            # Link activity to venue
            cursor.execute('''
                INSERT INTO activity_venues (activity_id, venue_id)
                VALUES (?, ?)
            ''', (activity_id, venue_id))
        
        conn.commit()
        print("Database initialized with AI-enhanced sample data!")
    
    conn.close()

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """Enhanced activities endpoint with AI features"""
    try:
        # Get query parameters
        location = request.args.get('location', '')
        duration = request.args.get('duration', '')
        filters = request.args.getlist('filters[]')
        mood_hint = request.args.get('mood_hint', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Enhanced query with AI fields
        query = '''
            SELECT DISTINCT 
                a.id, a.title, a.description, a.ai_enhanced_description,
                a.activity_type, a.duration_minutes, a.cost_category, 
                a.price_min, a.price_max, a.rating,
                a.joy_factors, a.parent_whisper, a.surprise_element,
                a.mood_tags, a.spontaneity_score,
                v.name as venue_name, v.address, v.city, v.is_open_now
            FROM activities a
            LEFT JOIN activity_venues av ON a.id = av.activity_id
            LEFT JOIN venues v ON av.venue_id = v.id
            WHERE a.is_active = 1
        '''
        
        params = []
        
        # Add location filter
        if location and location not in ['All Cities', '']:
            query += ' AND v.city LIKE ?'
            params.append(f'%{location}%')
        
        # Add mood-based filtering
        if mood_hint:
            mood_hint_lower = mood_hint.lower()
            if 'antsy' in mood_hint_lower or 'energy' in mood_hint_lower or 'bouncing' in mood_hint_lower:
                query += ' AND a.activity_type = "outdoor"'
            elif 'calm' in mood_hint_lower or 'quiet' in mood_hint_lower or 'peaceful' in mood_hint_lower:
                query += ' AND a.activity_type IN ("educational")'
            elif 'creative' in mood_hint_lower or 'art' in mood_hint_lower:
                query += ' AND (a.mood_tags LIKE "%creative%" OR a.activity_type = "educational")'
            elif 'curious' in mood_hint_lower or 'learn' in mood_hint_lower:
                query += ' AND a.activity_type = "educational"'
        
        # Enhanced duration filter
        if duration and duration not in ['Any', '']:
            if '30 min' in duration:
                query += ' AND a.duration_minutes <= 60'
            elif '1 hr' in duration:
                query += ' AND a.duration_minutes <= 90'
            elif '2 hrs' in duration:
                query += ' AND a.duration_minutes <= 180'
            elif '4+' in duration or 'All day' in duration:
                query += ' AND a.duration_minutes >= 240'
        
        # Apply filters
        if filters:
            filter_conditions = []
            for filter_name in filters:
                if filter_name == 'OUTDOOR':
                    filter_conditions.append("a.activity_type = 'outdoor'")
                elif filter_name == 'INDOOR':
                    filter_conditions.append("a.activity_type IN ('educational', 'recreational')")
                elif filter_name == 'FREE':
                    filter_conditions.append("a.cost_category = 'free'")
                elif filter_name == 'HIGHLY RATED':
                    filter_conditions.append("a.rating >= 4.5")
                elif filter_name == 'HAPPENING NOW':
                    filter_conditions.append("v.is_open_now = 1")
            
            if filter_conditions:
                query += ' AND (' + ' OR '.join(filter_conditions) + ')'
        
        # Sort by spontaneity score and rating
        query += ' ORDER BY a.spontaneity_score DESC, a.rating DESC LIMIT 20'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        activities = []
        for row in rows:
            activity = {
                'id': str(row['id']),
                'title': row['title'],
                'description': row['description'],
                'ai_enhanced_description': row['ai_enhanced_description'],
                'activity_type': row['activity_type'],
                'duration': format_duration(row['duration_minutes']),
                'duration_minutes': row['duration_minutes'],
                'cost_category': row['cost_category'],
                'price_min': row['price_min'],
                'price_max': row['price_max'],
                'venue_name': row['venue_name'],
                'address': row['address'],
                'city': row['city'],
                'rating': row['rating'] or 4.0,
                'is_open_now': bool(row['is_open_now']),
                
                # AI Enhancement Fields (the magic!)
                'joy_factors': json.loads(row['joy_factors']) if row['joy_factors'] else [],
                'parent_whisper': row['parent_whisper'] or '',
                'surprise_element': row['surprise_element'] or '',
                'mood_tags': json.loads(row['mood_tags']) if row['mood_tags'] else [],
                'spontaneity_score': row['spontaneity_score'] or 0.8,
                
                'source': 'database'
            }
            activities.append(activity)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities),
            'ai_enhanced': True,
            'message': f'Found {len(activities)} magical activities!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/api/activities/mood-search', methods=['POST'])
def mood_search():
    """Mood-based activity search"""
    try:
        data = request.json
        query = data.get('query', '')
        location = data.get('location', 'Berkeley')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query_sql = '''
            SELECT DISTINCT 
                a.id, a.title, a.description, a.ai_enhanced_description,
                a.activity_type, a.duration_minutes, a.cost_category, 
                a.price_min, a.price_max, a.rating,
                a.joy_factors, a.parent_whisper, a.surprise_element,
                a.mood_tags, a.spontaneity_score,
                v.name as venue_name, v.address, v.city, v.is_open_now
            FROM activities a
            LEFT JOIN activity_venues av ON a.id = av.activity_id
            LEFT JOIN venues v ON av.venue_id = v.id
            WHERE a.is_active = 1 AND v.city LIKE ?
        '''
        
        params = [f'%{location}%']
        query_lower = query.lower()
        
        # Add mood-based filtering
        if 'antsy' in query_lower or 'energy' in query_lower or 'bouncing' in query_lower or 'walls' in query_lower:
            query_sql += ' AND a.activity_type = "outdoor"'
        elif 'calm' in query_lower or 'quiet' in query_lower or 'peaceful' in query_lower:
            query_sql += ' AND a.activity_type = "educational"'
        elif 'creative' in query_lower or 'art' in query_lower or 'making' in query_lower:
            query_sql += ' AND a.activity_type = "educational"'
        elif 'curious' in query_lower or 'learn' in query_lower or 'questions' in query_lower:
            query_sql += ' AND a.activity_type = "educational"'
        
        query_sql += ' ORDER BY a.spontaneity_score DESC LIMIT 10'
        
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()
        
        activities = []
        for row in rows:
            activity = {
                'id': str(row['id']),
                'title': row['title'],
                'description': row['description'],
                'ai_enhanced_description': row['ai_enhanced_description'],
                'activity_type': row['activity_type'],
                'duration': format_duration(row['duration_minutes']),
                'duration_minutes': row['duration_minutes'],
                'cost_category': row['cost_category'],
                'venue_name': row['venue_name'],
                'address': row['address'],
                'city': row['city'],
                'rating': row['rating'] or 4.0,
                'is_open_now': bool(row['is_open_now']),
                'joy_factors': json.loads(row['joy_factors']) if row['joy_factors'] else [],
                'parent_whisper': row['parent_whisper'] or '',
                'surprise_element': row['surprise_element'] or '',
                'mood_tags': json.loads(row['mood_tags']) if row['mood_tags'] else [],
                'spontaneity_score': row['spontaneity_score'] or 0.8,
                'source': 'database'
            }
            activities.append(activity)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'query': query,
            'activities': activities,
            'count': len(activities)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'TOT TROT AI-Enhanced API is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0 - AI Enhanced',
        'features': [
            'AI-enhanced activity descriptions',
            'Joy factors and parent tips',
            'Mood-based search',
            'Spontaneity scoring'
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting Enhanced TOT TROT API...")
    print("🤖 AI enhancements: Joy factors, Parent tips, Mood matching")
    
    # Create tables
    create_tables()
    
    # Initialize with sample data
    init_database_with_sample_data()
    
    print("✅ Database ready with AI-enhanced activities!")
    print("📡 API endpoints:")
    print("   GET /api/activities - Enhanced activity search")
    print("   POST /api/activities/mood-search - Mood-based search")
    print("   GET /api/health - Health check")
    print("")
    
    # Run the server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
