-- Enhanced Database Schema for Rich Family Activity Data
-- Adds real-time data, user content, and dynamic features

-- Enhanced activities table with rich data fields
ALTER TABLE activities ADD COLUMN start_time DATETIME;
ALTER TABLE activities ADD COLUMN end_time DATETIME;
ALTER TABLE activities ADD COLUMN event_url TEXT;
ALTER TABLE activities ADD COLUMN image_url TEXT;
ALTER TABLE activities ADD COLUMN capacity INTEGER;
ALTER TABLE activities ADD COLUMN current_capacity INTEGER;
ALTER TABLE activities ADD COLUMN estimated_wait_time INTEGER;
ALTER TABLE activities ADD COLUMN popularity_score INTEGER DEFAULT 0;
ALTER TABLE activities ADD COLUMN demand_level TEXT DEFAULT 'low';
ALTER TABLE activities ADD COLUMN weather_dependent BOOLEAN DEFAULT 0;
ALTER TABLE activities ADD COLUMN seasonal_activity BOOLEAN DEFAULT 0;
ALTER TABLE activities ADD COLUMN status TEXT DEFAULT 'active';
ALTER TABLE activities ADD COLUMN last_capacity_update DATETIME;
ALTER TABLE activities ADD COLUMN last_price_update DATETIME;

-- User reviews and ratings
CREATE TABLE IF NOT EXISTS activity_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    user_name TEXT,
    user_email TEXT,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    review_text TEXT,
    review_title TEXT,
    age_of_child INTEGER,
    visit_date DATE,
    helpful_votes INTEGER DEFAULT 0,
    verified_visit BOOLEAN DEFAULT 0,
    photos TEXT, -- JSON array of photo URLs
    tips TEXT, -- JSON array of user tips
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- User-generated photos
CREATE TABLE IF NOT EXISTS activity_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    photo_url TEXT NOT NULL,
    caption TEXT,
    uploaded_by TEXT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    likes_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT 0,
    moderation_status TEXT DEFAULT 'pending',
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Real-time activity tracking
CREATE TABLE IF NOT EXISTS activity_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    user_session TEXT,
    view_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_location TEXT,
    referrer_source TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Activity bookings/check-ins
CREATE TABLE IF NOT EXISTS activity_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    user_email TEXT,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    visit_date DATE,
    party_size INTEGER,
    children_ages TEXT, -- JSON array of ages
    status TEXT DEFAULT 'confirmed',
    special_requests TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Weather conditions for outdoor activities
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    date DATE NOT NULL,
    temperature_high INTEGER,
    temperature_low INTEGER,
    weather_condition TEXT, -- sunny, cloudy, rainy, etc.
    precipitation_chance INTEGER,
    wind_speed INTEGER,
    air_quality_index INTEGER,
    uv_index INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, date)
);

-- Dynamic pricing history
CREATE TABLE IF NOT EXISTS pricing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    price_min DECIMAL(10,2),
    price_max DECIMAL(10,2),
    demand_level TEXT,
    weather_factor DECIMAL(3,2) DEFAULT 1.0,
    seasonal_factor DECIMAL(3,2) DEFAULT 1.0,
    effective_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Activity recommendations (AI-generated)
CREATE TABLE IF NOT EXISTS activity_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    recommended_activity_id INTEGER NOT NULL,
    recommendation_type TEXT, -- similar, nearby, complementary
    confidence_score DECIMAL(3,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- User favorites and wishlists
CREATE TABLE IF NOT EXISTS user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_session TEXT NOT NULL,
    activity_id INTEGER NOT NULL,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    UNIQUE(user_session, activity_id)
);

-- Activity availability schedules (for recurring events)
CREATE TABLE IF NOT EXISTS activity_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    day_of_week INTEGER, -- 0=Sunday, 1=Monday, etc.
    start_time TIME,
    end_time TIME,
    max_capacity INTEGER,
    current_bookings INTEGER DEFAULT 0,
    price_override DECIMAL(10,2),
    special_notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    effective_start_date DATE,
    effective_end_date DATE,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Seasonal activity data
CREATE TABLE IF NOT EXISTS seasonal_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    season TEXT NOT NULL, -- spring, summer, fall, winter
    start_date DATE,
    end_date DATE,
    seasonal_description TEXT,
    seasonal_pricing TEXT,
    seasonal_tags TEXT, -- JSON array
    is_holiday_special BOOLEAN DEFAULT 0,
    holiday_name TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Activity organizers/providers
CREATE TABLE IF NOT EXISTS activity_organizers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    website TEXT,
    social_media TEXT, -- JSON object with social links
    rating DECIMAL(3,2),
    verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Link activities to organizers
CREATE TABLE IF NOT EXISTS activity_organizer_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    organizer_id INTEGER NOT NULL,
    relationship_type TEXT DEFAULT 'organizer', -- organizer, venue, sponsor
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (organizer_id) REFERENCES activity_organizers(id) ON DELETE CASCADE
);

-- Activity check-ins (for real-time capacity)
CREATE TABLE IF NOT EXISTS activity_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    checkout_time DATETIME,
    party_size INTEGER DEFAULT 1,
    user_session TEXT,
    status TEXT DEFAULT 'active', -- active, completed
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities(start_time);
CREATE INDEX IF NOT EXISTS idx_activities_popularity ON activities(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_activities_demand ON activities(demand_level);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON activity_reviews(rating DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON activity_reviews(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_views_date ON activity_views(view_date);
CREATE INDEX IF NOT EXISTS idx_weather_city_date ON weather_data(city, date);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON user_favorites(user_session);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON activity_bookings(visit_date);

-- Views for common queries
CREATE VIEW IF NOT EXISTS popular_activities AS
SELECT 
    a.*,
    COALESCE(AVG(r.rating), 4.0) as avg_rating,
    COUNT(r.id) as review_count,
    v.view_count
FROM activities a
LEFT JOIN activity_reviews r ON a.id = r.activity_id
LEFT JOIN (
    SELECT activity_id, COUNT(*) as view_count
    FROM activity_views 
    WHERE view_date > datetime('now', '-7 days')
    GROUP BY activity_id
) v ON a.id = v.activity_id
WHERE a.is_active = 1
GROUP BY a.id
ORDER BY a.popularity_score DESC, avg_rating DESC;

CREATE VIEW IF NOT EXISTS current_capacity_status AS
SELECT 
    a.id,
    a.title,
    a.capacity,
    a.current_capacity,
    a.estimated_wait_time,
    CASE 
        WHEN a.current_capacity >= a.capacity * 0.9 THEN 'very_busy'
        WHEN a.current_capacity >= a.capacity * 0.7 THEN 'busy'
        WHEN a.current_capacity >= a.capacity * 0.4 THEN 'moderate'
        ELSE 'available'
    END as capacity_status,
    a.last_capacity_update
FROM activities a
WHERE a.capacity IS NOT NULL
AND a.is_active = 1;

-- Triggers for automatic updates
CREATE TRIGGER IF NOT EXISTS update_activity_popularity
AFTER INSERT ON activity_views
BEGIN
    UPDATE activities 
    SET popularity_score = (
        SELECT COUNT(*) FROM activity_views 
        WHERE activity_id = NEW.activity_id 
        AND view_date > datetime('now', '-7 days')
    )
    WHERE id = NEW.activity_id;
END;

CREATE TRIGGER IF NOT EXISTS update_capacity_on_checkin
AFTER INSERT ON activity_checkins
BEGIN
    UPDATE activities 
    SET current_capacity = current_capacity + NEW.party_size,
        last_capacity_update = datetime('now')
    WHERE id = NEW.activity_id;
END;

CREATE TRIGGER IF NOT EXISTS update_capacity_on_checkout
AFTER UPDATE ON activity_checkins
WHEN NEW.status = 'completed' AND OLD.status = 'active'
BEGIN
    UPDATE activities 
    SET current_capacity = current_capacity - NEW.party_size,
        last_capacity_update = datetime('now')
    WHERE id = NEW.activity_id;
END;
