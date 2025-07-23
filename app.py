# Backend API Server for Family Activity App
# Enhanced with multi-city collection and smart duration logic
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
    
    # Create activities table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            activity_type TEXT NOT NULL,
            min_age INTEGER,
            max_age INTEGER,
            duration_minutes INTEGER DEFAULT 120,
            cost_category TEXT DEFAULT 'unknown',
            price_min DECIMAL(10,2),
            price_max DECIMAL(10,2),
            difficulty_level TEXT,
            group_size_min INTEGER DEFAULT 1,
            group_size_max INTEGER,
            rating REAL DEFAULT 4.0,
            popularity_score INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create venues table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            venue_type TEXT NOT NULL,
            address TEXT,
            city TEXT NOT NULL,
            state TEXT DEFAULT 'CA',
            zip_code TEXT,
            country TEXT DEFAULT 'US',
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            phone TEXT,
            website TEXT,
            google_place_id TEXT,
            google_url TEXT,
            rating DECIMAL(3,2),
            is_wheelchair_accessible BOOLEAN DEFAULT 0,
            parking_available BOOLEAN DEFAULT 0,
            business_status TEXT,
            opening_hours TEXT,
            is_open_now BOOLEAN DEFAULT 1,
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
    
    # Create activity photos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            photo_url TEXT NOT NULL,
            caption TEXT,
            uploaded_by TEXT,
            moderation_status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    ''')
    
    # Create activity reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            visit_date DATE,
            helpful_votes INTEGER DEFAULT 0,
            verified_visit BOOLEAN DEFAULT 0,
            age_of_child INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
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

def update_schema():
    """Add missing columns for enhanced functionality"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Add columns that might be missing
        new_columns = [
            ('activities', 'rating', 'REAL DEFAULT 4.0'),
            ('activities', 'popularity_score', 'INTEGER DEFAULT 0'),
            ('venues', 'google_place_id', 'TEXT'),
            ('venues', 'google_url', 'TEXT'),
            ('venues', 'business_status', 'TEXT'),
            ('venues', 'opening_hours', 'TEXT'),
            ('venues', 'is_open_now', 'BOOLEAN DEFAULT 1'),
            ('venues', 'phone', 'TEXT'),
            ('venues', 'website', 'TEXT')
        ]
        
        for table, column, definition in new_columns:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
                print(f"Added {column} to {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"Error adding {column} to {table}: {e}")
        
        conn.commit()
        print("Schema update completed!")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
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
        
        # Enhanced sample activities with smart duration
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
                'popularity_score': 85,
                'tags': ['outdoor', 'nature', 'hiking', 'playground', 'free', 'family_friendly', 'full_day']
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
                'popularity_score': 95,
                'tags': ['indoor', 'educational', 'science', 'animals', 'rainy_day', 'full_day']
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
                'popularity_score': 60,
                'tags': ['indoor', 'educational', 'toddler_friendly', 'free', 'reading', 'quick_visit']
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
                'popularity_score': 75,
                'tags': ['outdoor', 'playground', 'free', 'physical', 'toddler_friendly', 'half_day']
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
                'popularity_score': 80,
                'tags': ['outdoor', 'educational', 'animals', 'family_friendly', 'full_day']
            }
        ]
        
        # Insert activities and related data
        for activity in sample_activities:
            cursor.execute('''
                INSERT INTO activities 
                (title, description, activity_type, min_age, max_age, duration_minutes, 
                 cost_category, price_min, price_max, rating, popularity_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity['title'], activity['description'], activity['activity_type'],
                activity['min_age'], activity['max_age'], activity['duration_minutes'],
                activity['cost_category'], activity['price_min'], activity['price_max'],
                activity['rating'], activity['popularity_score'], datetime.now(), datetime.now()
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
        print("Database initialized with enhanced sample data!")
    else:
        print(f"Database already has {count} activities")
    
    conn.close()

@app.route('/api/activities', methods=['GET'])
def get_activities():
    """Get activities based on filters with enhanced duration logic"""
    try:
        # Get query parameters
        location = request.args.get('location', '')
        duration = request.args.get('duration', '')
        filters = request.args.getlist('filters[]')
        child_age = request.args.get('child_age', type=int)
        sort_by = request.args.get('sort_by', 'rating')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Enhanced query with new fields
        query = '''
            SELECT DISTINCT 
                a.id, a.title, a.description, a.activity_type,
                a.min_age, a.max_age, a.duration_minutes,
                a.cost_category, a.price_min, a.price_max,
                a.rating, a.popularity_score,
                v.name as venue_name, v.address, v.city, 
                v.latitude, v.longitude, v.phone, v.website,
                v.is_open_now, v.business_status,
                GROUP_CONCAT(DISTINCT t.name) as tags,
                COUNT(DISTINCT r.id) as review_count
            FROM activities a
            LEFT JOIN activity_venues av ON a.id = av.activity_id
            LEFT JOIN venues v ON av.venue_id = v.id
            LEFT JOIN activity_tags at ON a.id = at.activity_id
            LEFT JOIN tags t ON at.tag_id = t.id
            LEFT JOIN activity_reviews r ON a.id = r.activity_id
            WHERE a.is_active = 1
        '''
        
        params = []
        
        # Add location filter
        if location and location not in ['All Cities', '']:
            query += ' AND v.city LIKE ?'
            params.append(f'%{location}%')
        
        # Add age filter
        if child_age:
            query += ' AND (a.min_age IS NULL OR a.min_age <= ?) AND (a.max_age IS NULL OR a.max_age >= ?)'
            params.extend([child_age, child_age])
        
        # Enhanced duration filter with smart matching
        if duration and duration not in ['Any', '']:
            if '30 min' in duration:
                query += ' AND a.duration_minutes <= 60'
            elif '1 hr' in duration:
                query += ' AND a.duration_minutes <= 90'
            elif '2 hrs' in duration:
                query += ' AND a.duration_minutes <= 180'
            elif '4+' in duration or 'All day' in duration:
                query += ' AND a.duration_minutes >= 240'
        
        query += ' GROUP BY a.id'
        
        # Enhanced filter processing
        if filters:
            having_conditions = []
            for filter_name in filters:
                if filter_name == 'OUTDOOR':
                    having_conditions.append("a.activity_type = 'outdoor'")
                elif filter_name == 'INDOOR':
                    having_conditions.append("(a.activity_type IN ('educational', 'recreational') OR tags LIKE '%indoor%')")
                elif filter_name == 'FREE':
                    having_conditions.append("a.cost_category = 'free'")
                elif filter_name == 'LOW ENERGY':
                    having_conditions.append("(tags LIKE '%calming%' OR a.activity_type = 'educational' OR tags LIKE '%reading%')")
                elif filter_name == 'HIGH ENERGY':
                    having_conditions.append("(tags LIKE '%physical%' OR a.activity_type = 'outdoor' OR tags LIKE '%playground%')")
                elif filter_name == 'UNDER $25':
                    having_conditions.append("(a.price_max IS NULL OR a.price_max < 25)")
                elif filter_name == '$25+':
                    having_conditions.append("a.price_min >= 25")
                elif filter_name == 'HIGHLY RATED':
                    having_conditions.append("a.rating >= 4.5")
                elif filter_name == 'HAPPENING NOW':
                    having_conditions.append("v.is_open_now = 1")
            
            if having_conditions:
                query += ' HAVING ' + ' OR '.join(having_conditions)
        
        # Enhanced sorting
        if sort_by == 'rating':
            query += ' ORDER BY a.rating DESC, a.popularity_score DESC'
        elif sort_by == 'popularity':
            query += ' ORDER BY a.popularity_score DESC, a.rating DESC'
        elif sort_by == 'price':
            query += ' ORDER BY COALESCE(a.price_min, 0) ASC'
        elif sort_by == 'distance':
            query += ' ORDER BY v.city, a.title'
        else:
            query += ' ORDER BY a.rating DESC'
        
        query += ' LIMIT 50'  # Increased limit
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        activities = []
        for row in rows:
            # Smart duration formatting
            duration_minutes = row['duration_minutes'] or 120
            if duration_minutes <= 45:
                duration_display = "30-45 min"
                duration_category = "quick"
            elif duration_minutes <= 90:
                duration_display = "1-1.5 hrs"
                duration_category = "short"
            elif duration_minutes <= 180:
                duration_display = "2-3 hrs"
                duration_category = "medium"
            elif duration_minutes <= 300:
                duration_display = "4-5 hrs"
                duration_category = "long"
            else:
                duration_display = "All day"
                duration_category = "full_day"
            
            activity = {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'activity_type': row['activity_type'],
                'duration': duration_display,
                'duration_minutes': duration_minutes,
                'duration_category': duration_category,
                'cost_category': row['cost_category'],
                'price_min': row['price_min'],
                'price_max': row['price_max'],
                'venue_name': row['venue_name'],
                'address': row['address'],
                'city': row['city'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'phone': row['phone'],
                'website': row['website'],
                'rating': row['rating'] or 4.0,
                'popularity_score': row['popularity_score'] or 0,
                'review_count': row['review_count'] or 0,
                'is_open_now': bool(row['is_open_now']),
                'business_status': row['business_status'],
                'tags': row['tags'].split(',') if row['tags'] else [],
                'category': row['activity_type']  # For compatibility
            }
            activities.append(activity)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities),
            'filters_applied': filters,
            'location': location,
            'duration': duration
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/activities/enhanced', methods=['GET'])
def get_enhanced_activities():
    """Get activities with all enhanced data including photos and reviews"""
    try:
        location = request.args.get('location', '')
        duration = request.args.get('duration', '')
        filters = request.args.getlist('filters[]')
        sort_by = request.args.get('sort_by', 'rating')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get activities with photos and reviews
        query = '''
            SELECT DISTINCT 
                a.*,
                v.name as venue_name, v.address, v.city, 
                v.latitude, v.longitude, v.phone, v.website,
                v.is_open_now, v.business_status,
                GROUP_CONCAT(DISTINCT t.name) as tags,
                GROUP_CONCAT(DISTINCT p.photo_url) as photos,
                AVG(r.rating) as avg_rating,
                COUNT(DISTINCT r.id) as review_count
            FROM activities a
            LEFT JOIN activity_venues av ON a.id = av.activity_id
            LEFT JOIN venues v ON av.venue_id = v.id
            LEFT JOIN activity_tags at ON a.id = at.activity_id
            LEFT JOIN tags t ON at.tag_id = t.id
            LEFT JOIN activity_photos p ON a.id = p.activity_id AND p.moderation_status = 'approved'
            LEFT JOIN activity_reviews r ON a.id = r.activity_id
            WHERE a.is_active = 1
        '''
        
        params = []
        
        if location and location not in ['All Cities', '']:
            query += ' AND v.city LIKE ?'
            params.append(f'%{location}%')
        
        query += ' GROUP BY a.id ORDER BY a.rating DESC LIMIT 20'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        activities = []
        for row in rows:
            activity = dict(row)
            activity['photos'] = row['photos'].split(',') if row['photos'] else []
            activity['tags'] = row['tags'].split(',') if row['tags'] else []
            activity['reviews'] = []  # Could fetch reviews separately if needed
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
        # Return hardcoded cities that match our multi-city collector
        locations = ['Berkeley', 'San Francisco', 'Oakland', 'San Jose', 'Palo Alto']
        
        return jsonify({
            'success': True,
            'locations': locations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/<city>', methods=['GET'])
def get_weather(city):
    """Get weather data for a city"""
    try:
        # Simple weather simulation - in production would use real weather API
        import random
        
        weather_conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain']
        
        weather_data = {
            'temperature_high': random.randint(60, 80),
            'weather_condition': random.choice(weather_conditions),
            'precipitation_chance': random.randint(0, 40)
        }
        
        return jsonify({
            'success': True,
            'weather': weather_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get enhanced database statistics"""
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
        
        # Activities by duration category
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN duration_minutes <= 60 THEN 'Quick (≤1hr)'
                    WHEN duration_minutes <= 180 THEN 'Medium (1-3hrs)'
                    WHEN duration_minutes <= 300 THEN 'Long (3-5hrs)'
                    ELSE 'Full Day (5+hrs)'
                END as duration_category,
                COUNT(*) as count
            FROM activities 
            WHERE is_active = 1
            GROUP BY 
                CASE 
                    WHEN duration_minutes <= 60 THEN 'Quick (≤1hr)'
                    WHEN duration_minutes <= 180 THEN 'Medium (1-3hrs)'
                    WHEN duration_minutes <= 300 THEN 'Long (3-5hrs)'
                    ELSE 'Full Day (5+hrs)'
                END
        ''')
        duration_categories = dict(cursor.fetchall())
        
        # Cost distribution
        cursor.execute('''
            SELECT cost_category, COUNT(*) as count
            FROM activities 
            WHERE is_active = 1
            GROUP BY cost_category
        ''')
        cost_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_activities': total_activities,
                'activity_types': activity_types,
                'cities': cities,
                'duration_categories': duration_categories,
                'cost_distribution': cost_distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/track/view', methods=['POST'])
def track_activity_view():
    """Track when someone views an activity"""
    try:
        data = request.json
        # In a real app, you'd save this to analytics
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/favorites', methods=['POST'])
def handle_favorites():
    """Handle adding/removing favorites"""
    try:
        data = request.json
        # In a real app, you'd save to user_favorites table
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Family Activity API is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

# Collection endpoints
@app.route('/api/collect/multi-city-smart', methods=['GET'])
def collect_multi_city_smart():
    """Collect comprehensive data for all cities with smart duration"""
    try:
        from multi_city_smart_collector import run_multi_city_smart_collection
        result = run_multi_city_smart_collection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/collect/berkeley-expanded', methods=['GET'])
def collect_berkeley_expanded():
    """Collect comprehensive Berkeley area data"""
    try:
        from expanded_berkeley_collector import run_expanded_berkeley_collection
        result = run_expanded_berkeley_collection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Something went wrong on our end'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced Family Activity API...")
    print("📊 Features: Multi-city data, Smart duration, Enhanced filtering")
    
    # Create tables first
    create_tables()
    
    # Update schema for any missing columns
    update_schema()
    
    # Initialize database with sample data
    init_database()
    
    print("✅ Database initialized successfully!")
    print("🌐 Available cities: Berkeley, San Francisco, Oakland, San Jose, Palo Alto")
    print("⏱️  Smart duration matching enabled")
    print("🔍 Enhanced filtering and search ready")
    
    # Run the server
    port = int(os.environ.get('PORT', 5000))
    print(f"🎯 Server running on port {port}")
    print("📡 API endpoints:")
    print(f"   GET /api/health - Health check")
    print(f"   GET /api/activities - Get filtered activities")
    print(f"   GET /api/activities/enhanced - Get activities with photos/reviews")
    print(f"   GET /api/locations - Get available cities")
    print(f"   GET /api/stats - Get database statistics")
    print(f"   GET /api/collect/multi-city-smart - Collect comprehensive data")
    print(f"   GET /api/weather/<city> - Get weather for city")
    print("")
    
    app.run(host='0.0.0.0', port=port, debug=True)
