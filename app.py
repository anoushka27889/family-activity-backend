# Backend API Server for Family Activity App
# This connects your React app to the SQLite database with real activity data
from simple_google_collector import run_simple_google_collection
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Allow requests from your React app

# Database configuration
DATABASE_PATH = 'activities.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def create_tables():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            activity_type TEXT NOT NULL,
            min_age INTEGER,
            max_age INTEGER,
            duration_minutes INTEGER,
            cost_category TEXT DEFAULT 'unknown',
            price_min DECIMAL(10,2),
            price_max DECIMAL(10,2),
            difficulty_level TEXT,
            group_size_min INTEGER DEFAULT 1,
            group_size_max INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create venues table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            venue_type TEXT NOT NULL,
            address TEXT,
            city TEXT NOT NULL,
            state TEXT,
            zip_code TEXT,
            country TEXT DEFAULT 'US',
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            phone TEXT,
            website TEXT,
            rating DECIMAL(3,2),
            is_wheelchair_accessible BOOLEAN DEFAULT 0,
            parking_available BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create data sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            base_url TEXT,
            api_key_required BOOLEAN DEFAULT 0,
            rate_limit_per_hour INTEGER,
            last_updated DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            description TEXT
        )
    ''')
    
    # Create junction tables
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            UNIQUE(activity_id, tag_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            source_id INTEGER NOT NULL,
            external_id TEXT,
            source_url TEXT,
            last_scraped DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES data_sources(id) ON DELETE CASCADE,
            UNIQUE(activity_id, source_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully!")
    
def enhance_database():
    """Run database enhancements"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read and execute the enhancement SQL
    try:
        with open('enhance_database.sql', 'r') as f:
            sql_commands = f.read()
            cursor.executescript(sql_commands)
        conn.commit()
        print("Database enhanced successfully!")
    except Exception as e:
        print(f"Enhancement error: {e}")
    finally:
        conn.close()
        
def init_database():
    """Initialize database with sample data if empty"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we have any activities
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Initializing database with sample data...")
        
        # Insert sample data sources first
        cursor.execute('''
            INSERT INTO data_sources (name, source_type, base_url, api_key_required)
            VALUES ('Sample Data', 'manual', NULL, 0)
        ''')
        source_id = cursor.lastrowid
        
        # Insert sample activities
        sample_activities = [
            {
                'title': 'Tilden Nature Area',
                'description': 'Beautiful hiking trails, playground, and nature center with easy walks for families.',
                'activity_type': 'outdoor',
                'min_age': 0,
                'max_age': 18,
                'duration_minutes': 240,
                'cost_category': 'free',
                'price_min': 0,
                'price_max': 0,
                'city': 'Berkeley',
                'venue_name': 'Tilden Regional Park',
                'address': 'Berkeley Hills, Berkeley, CA',
                'latitude': 37.8917,
                'longitude': -122.2436,
                'rating': 4.8,
                'tags': ['outdoor', 'nature', 'hiking', 'playground', 'free', 'family_friendly']
            },
            {
                'title': "Children's Discovery Museum",
                'description': 'Interactive exhibits designed for curious minds with hands-on science and art areas.',
                'activity_type': 'educational',
                'min_age': 2,
                'max_age': 12,
                'duration_minutes': 180,
                'cost_category': 'medium',
                'price_min': 15,
                'price_max': 20,
                'city': 'San Jose',
                'venue_name': "Children's Discovery Museum",
                'address': '180 Woz Way, San Jose, CA',
                'latitude': 37.3275,
                'longitude': -121.8925,
                'rating': 4.5,
                'tags': ['indoor', 'educational', 'hands_on', 'rainy_day', 'toddler_friendly']
            },
            {
                'title': 'Berkeley Public Library Story Time',
                'description': 'Weekly interactive story sessions with songs and activities for young children.',
                'activity_type': 'educational',
                'min_age': 1,
                'max_age': 5,
                'duration_minutes': 45,
                'cost_category': 'free',
                'price_min': 0,
                'price_max': 0,
                'city': 'Berkeley',
                'venue_name': 'Berkeley Public Library',
                'address': '2090 Kittredge St, Berkeley, CA',
                'latitude': 37.8699,
                'longitude': -122.2678,
                'rating': 4.3,
                'tags': ['indoor', 'educational', 'toddler_friendly', 'free', 'reading']
            },
            {
                'title': 'Bay Area Discovery Museum',
                'description': 'Hands-on exhibits and programs designed specifically for children 0-10 years old.',
                'activity_type': 'educational',
                'min_age': 0,
                'max_age': 10,
                'duration_minutes': 240,
                'cost_category': 'medium',
                'price_min': 18,
                'price_max': 18,
                'city': 'Sausalito',
                'venue_name': 'Bay Area Discovery Museum',
                'address': '557 McReynolds Rd, Sausalito, CA',
                'latitude': 37.8319,
                'longitude': -122.4933,
                'rating': 4.6,
                'tags': ['indoor', 'educational', 'hands_on', 'toddler_friendly']
            },
            {
                'title': 'Golden Gate Park Playground',
                'description': 'Large playground with climbing structures, swings, and open space for running.',
                'activity_type': 'outdoor',
                'min_age': 1,
                'max_age': 12,
                'duration_minutes': 120,
                'cost_category': 'free',
                'price_min': 0,
                'price_max': 0,
                'city': 'San Francisco',
                'venue_name': 'Golden Gate Park',
                'address': 'Golden Gate Park, San Francisco, CA',
                'latitude': 37.7694,
                'longitude': -122.4862,
                'rating': 4.4,
                'tags': ['outdoor', 'playground', 'free', 'physical', 'toddler_friendly']
            },
            {
                'title': 'California Academy of Sciences',
                'description': 'Natural history museum with aquarium, planetarium, and rainforest dome.',
                'activity_type': 'educational',
                'min_age': 3,
                'max_age': 18,
                'duration_minutes': 300,
                'cost_category': 'high',
                'price_min': 40,
                'price_max': 45,
                'city': 'San Francisco',
                'venue_name': 'California Academy of Sciences',
                'address': '55 Music Concourse Dr, San Francisco, CA',
                'latitude': 37.7699,
                'longitude': -122.4661,
                'rating': 4.7,
                'tags': ['indoor', 'educational', 'science', 'animals', 'rainy_day']
            },
            {
                'title': 'Crissy Field Beach',
                'description': 'Sandy beach with Golden Gate Bridge views, perfect for picnics and kite flying.',
                'activity_type': 'outdoor',
                'min_age': 0,
                'max_age': 18,
                'duration_minutes': 180,
                'cost_category': 'free',
                'price_min': 0,
                'price_max': 0,
                'city': 'San Francisco',
                'venue_name': 'Crissy Field',
                'address': 'Crissy Field, San Francisco, CA',
                'latitude': 37.8024,
                'longitude': -122.4662,
                'rating': 4.5,
                'tags': ['outdoor', 'beach', 'free', 'nature', 'family_friendly']
            },
            {
                'title': 'Aquarium of the Bay',
                'description': 'Walk-through tunnels with sharks, rays, and local marine life.',
                'activity_type': 'educational',
                'min_age': 2,
                'max_age': 18,
                'duration_minutes': 120,
                'cost_category': 'medium',
                'price_min': 25,
                'price_max': 30,
                'city': 'San Francisco',
                'venue_name': 'Aquarium of the Bay',
                'address': 'Pier 39, San Francisco, CA',
                'latitude': 37.8086,
                'longitude': -122.4098,
                'rating': 4.2,
                'tags': ['indoor', 'educational', 'animals', 'marine_life', 'rainy_day']
            },
            {
                'title': 'Oakland Zoo',
                'description': 'Home to over 700 native and exotic animals with interactive experiences.',
                'activity_type': 'educational',
                'min_age': 0,
                'max_age': 18,
                'duration_minutes': 240,
                'cost_category': 'medium',
                'price_min': 20,
                'price_max': 25,
                'city': 'Oakland',
                'venue_name': 'Oakland Zoo',
                'address': '9777 Golf Links Rd, Oakland, CA',
                'latitude': 37.7329,
                'longitude': -122.1468,
                'rating': 4.3,
                'tags': ['outdoor', 'educational', 'animals', 'family_friendly']
            },
            {
                'title': 'Chabot Space & Science Center',
                'description': 'Interactive science exhibits, planetarium shows, and telescope viewing.',
                'activity_type': 'educational',
                'min_age': 4,
                'max_age': 18,
                'duration_minutes': 180,
                'cost_category': 'medium',
                'price_min': 15,
                'price_max': 20,
                'city': 'Oakland',
                'venue_name': 'Chabot Space & Science Center',
                'address': '10000 Skyline Blvd, Oakland, CA',
                'latitude': 37.8183,
                'longitude': -122.1810,
                'rating': 4.4,
                'tags': ['indoor', 'educational', 'science', 'space', 'rainy_day']
            }
        ]
        
        # Insert activities
        for activity in sample_activities:
            cursor.execute('''
                INSERT INTO activities 
                (title, description, activity_type, min_age, max_age, duration_minutes, 
                 cost_category, price_min, price_max, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['title'], activity['description'], activity['activity_type'],
                activity['min_age'], activity['max_age'], activity['duration_minutes'],
                activity['cost_category'], activity['price_min'], activity['price_max'],
                datetime.now(), datetime.now()
            ))
            
            activity_id = cursor.lastrowid
            
            # Insert venue
            cursor.execute('''
                INSERT INTO venues 
                (name, address, city, latitude, longitude, rating, venue_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['venue_name'], activity['address'], activity['city'],
                activity['latitude'], activity['longitude'], activity['rating'],
                activity['activity_type'], datetime.now(), datetime.now()
            ))
            
            venue_id = cursor.lastrowid
            
            # Link activity to venue
            cursor.execute('''
                INSERT INTO activity_venues (activity_id, venue_id)
                VALUES (?, ?)
            ''', (activity_id, venue_id))
            
            # Link activity to data source
            cursor.execute('''
                INSERT INTO activity_sources (activity_id, source_id, external_id, source_url)
                VALUES (?, ?, ?, ?)
            ''', (activity_id, source_id, f'sample_{activity_id}', 'sample_data'))
            
            # Insert tags
            for tag_name in activity['tags']:
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
        print("Database initialized with sample data!")
    else:
        print(f"Database already has {count} activities")
    
    conn.close()






@app.route('/api/activities', methods=['GET'])
def get_activities():
    """Get activities based on filters"""
    try:
        # Get query parameters
        location = request.args.get('location', '')
        duration = request.args.get('duration', '')
        filters = request.args.getlist('filters[]')  # Multiple filters
        child_age = request.args.get('child_age', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query with joins
        query = '''
            SELECT DISTINCT 
                a.id, a.title, a.description, a.activity_type,
                a.min_age, a.max_age, a.duration_minutes,
                a.cost_category, a.price_min, a.price_max,
                v.name as venue_name, v.address, v.city, 
                v.latitude, v.longitude, v.rating,
                GROUP_CONCAT(t.name) as tags
            FROM activities a
            LEFT JOIN activity_venues av ON a.id = av.activity_id
            LEFT JOIN venues v ON av.venue_id = v.id
            LEFT JOIN activity_tags at ON a.id = at.activity_id
            LEFT JOIN tags t ON at.tag_id = t.id
            WHERE a.is_active = 1
        '''
        
        params = []
        
        # Add location filter
        if location and location != 'All Cities':
            query += ' AND v.city LIKE ?'
            params.append(f'%{location}%')
        
        # Add age filter
        if child_age:
            query += ' AND (a.min_age IS NULL OR a.min_age <= ?) AND (a.max_age IS NULL OR a.max_age >= ?)'
            params.extend([child_age, child_age])
        
        # Add duration filter (simplified)
        if duration and duration != 'Any':
            if '30 min' in duration:
                query += ' AND a.duration_minutes <= 30'
            elif '1 hr' in duration:
                query += ' AND a.duration_minutes <= 60'
            elif '2 hrs' in duration:
                query += ' AND a.duration_minutes <= 120'
        
        query += ' GROUP BY a.id'
        
        # Add filter-based WHERE conditions after GROUP BY
        if filters:
            having_conditions = []
            for filter_name in filters:
                if filter_name == 'OUTDOOR':
                    having_conditions.append("a.activity_type = 'outdoor'")
                elif filter_name == 'INDOOR':
                    having_conditions.append("a.activity_type IN ('educational', 'recreational') OR tags LIKE '%indoor%'")
                elif filter_name == 'FREE':
                    having_conditions.append("a.cost_category = 'free'")
                elif filter_name == 'LOW ENERGY':
                    having_conditions.append("tags LIKE '%calming%' OR a.activity_type = 'educational'")
                elif filter_name == 'HIGH ENERGY':
                    having_conditions.append("tags LIKE '%physical%' OR a.activity_type = 'outdoor'")
                elif filter_name == 'UNDER $20':
                    having_conditions.append("(a.price_max IS NULL OR a.price_max < 20)")
                elif filter_name == '$20+':
                    having_conditions.append("a.price_min >= 20")
            
            if having_conditions:
                query += ' HAVING ' + ' OR '.join(having_conditions)
        
        query += ' ORDER BY v.rating DESC, a.title'
        query += ' LIMIT 20'  # Limit results
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        activities = []
        for row in rows:
            activity = {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'activity_type': row['activity_type'],
                'duration': f"{row['duration_minutes']} min" if row['duration_minutes'] else "Flexible",
                'cost_category': row['cost_category'],
                'price_min': row['price_min'],
                'price_max': row['price_max'],
                'venue_name': row['venue_name'],
                'address': row['address'],
                'city': row['city'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'rating': row['rating'] or 4.0,
                'tags': row['tags'].split(',') if row['tags'] else [],
                'category': row['activity_type']  # For compatibility with frontend
            }
            activities.append(activity)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get available cities/locations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT city 
            FROM venues 
            WHERE city IS NOT NULL AND city != ''
            ORDER BY city
        ''')
        
        rows = cursor.fetchall()
        locations = [row['city'] for row in rows]
        conn.close()
        
        return jsonify({
            'success': True,
            'locations': locations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total activities
        cursor.execute('SELECT COUNT(*) FROM activities WHERE is_active = 1')
        total_activities = cursor.fetchone()[0]
        
        # Activities by type
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count 
            FROM activities 
            WHERE is_active = 1 
            GROUP BY activity_type
        ''')
        activity_types = dict(cursor.fetchall())
        
        # Activities by city
        cursor.execute('''
            SELECT v.city, COUNT(*) as count
            FROM activities a
            JOIN activity_venues av ON a.id = av.activity_id
            JOIN venues v ON av.venue_id = v.id
            WHERE a.is_active = 1
            GROUP BY v.city
            ORDER BY count DESC
        ''')
        cities = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_activities': total_activities,
                'activity_types': activity_types,
                'cities': cities
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Family Activity API is running!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/collect/google-places', methods=['GET', 'POST'])
def collect_google_places_fixed():
    """Fixed Google Places collection - much more reliable"""
    try:
        from simple_google_collector import run_simple_google_collection
        result = run_simple_google_collection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Collection failed'
        }), 500


if __name__ == '__main__':
    print("Starting Family Activity API...")
    
    # Create tables first
    create_tables()
    enhance_database()  # Add this line
    # Initialize database with sample data
    init_database()
    
    # Run the server
    port = int(os.environ.get('PORT', 5000))
    print(f"Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
