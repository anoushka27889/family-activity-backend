import { useState, useEffect } from 'react';

interface Activity {
  id: number;
  title: string;
  description: string;
  duration: string;
  tags: string[];
  rating: number;
  category: string;
  cost_category: string;
  price_min?: number;
  price_max?: number;
  venue_name?: string;
  address?: string;
  city?: string;
  image_url?: string;
  start_time?: string;
  end_time?: string;
  capacity?: number;
  current_capacity?: number;
  estimated_wait_time?: number;
  popularity_score?: number;
  demand_level?: string;
  weather_dependent?: boolean;
  reviews?: Review[];
  photos?: string[];
  organizer?: string;
  availability_status?: string;
  capacity_status?: string;
  similar_activities?: number[];
}

interface Review {
  id: number;
  user_name: string;
  rating: number;
  review_text: string;
  visit_date: string;
  helpful_votes: number;
  age_of_child?: number;
  photos?: string[];
  tips?: string[];
}

interface WeatherData {
  temperature_high: number;
  weather_condition: string;
  precipitation_chance: number;
}

// Your live API URL
const API_BASE_URL = 'https://family-activity-api.onrender.com/api';

function App() {
  const [currentScreen, setCurrentScreen] = useState('main');
  const [selectedLocation, setSelectedLocation] = useState('San Francisco');
  const [selectedDuration, setSelectedDuration] = useState('2 hrs');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [availableLocations, setAvailableLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<number[]>([]);
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid');
  const [sortBy, setSortBy] = useState<'rating' | 'popularity' | 'price' | 'distance'>('rating');

  const filterOptions = [
    'OUTDOOR', 'INDOOR', 'FREE', 'LOW ENERGY', 'HIGH ENERGY', 
    'UNDER $25', '$25+', 'HAPPENING NOW', 'AVAILABLE SPOTS', 'HIGHLY RATED'
  ];

  // Available locations - expanded to match collector
  const cityOptions = ['Berkeley', 'San Francisco', 'Oakland', 'San Jose', 'Palo Alto'];
  
  // Smart duration options with better logic
  const durationOptions = [
    { value: '30 min', label: '30 min', category: 'quick' },
    { value: '1 hr', label: '1 hr', category: 'short' },
    { value: '2 hrs', label: '2 hrs', category: 'medium' },
    { value: '4+ hrs', label: '4+ hrs', category: 'long' },
    { value: 'All day', label: 'All day', category: 'full_day' }
  ];

  // Load favorites from localStorage on mount
  useEffect(() => {
    const savedFavorites = localStorage.getItem('familyapp_favorites');
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
    fetchLocations();
    fetchWeatherData();
  }, []);

  const fetchWeatherData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/${selectedLocation}`);
      const data = await response.json();
      if (data.success) {
        setWeatherData(data.weather);
      }
    } catch (err) {
      console.error('Failed to fetch weather:', err);
    }
  };

  const fetchLocations = async () => {
    try {
      setAvailableLocations(cityOptions);
    } catch (err) {
      console.error('Failed to fetch locations:', err);
      setAvailableLocations(cityOptions);
    }
  };

  const fetchActivities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      params.append('location', selectedLocation);
      params.append('duration', selectedDuration);
      params.append('sort_by', sortBy);
      
      selectedFilters.forEach(filter => {
        params.append('filters[]', filter);
      });

      const response = await fetch(`${API_BASE_URL}/activities/enhanced?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setActivities(data.activities);
        setCurrentScreen('results');
        
        // Track page view for analytics
        trackPageView('search_results', { location: selectedLocation, filters: selectedFilters });
      } else {
        setError(data.error || 'Failed to fetch activities');
      }
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError('Unable to connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (activityId: number) => {
    const newFavorites = favorites.includes(activityId)
      ? favorites.filter(id => id !== activityId)
      : [...favorites, activityId];
    
    setFavorites(newFavorites);
    localStorage.setItem('familyapp_favorites', JSON.stringify(newFavorites));
    
    // Send to API for tracking
    fetch(`${API_BASE_URL}/favorites`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activity_id: activityId, action: favorites.includes(activityId) ? 'remove' : 'add' })
    });
  };

  const trackActivityView = (activityId: number) => {
    fetch(`${API_BASE_URL}/track/view`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        activity_id: activityId, 
        location: selectedLocation,
        timestamp: new Date().toISOString()
      })
    });
  };

  const trackPageView = (page: string, data: any) => {
    fetch(`${API_BASE_URL}/track/page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page, data, timestamp: new Date().toISOString() })
    });
  };

  const toggleFilter = (filter: string) => {
    setSelectedFilters(prev => 
      prev.includes(filter) 
        ? prev.filter(f => f !== filter)
        : [...prev, filter]
    );
  };

  const handleSearch = () => {
    fetchActivities();
  };

  const formatPrice = (activity: Activity) => {
    if (activity.cost_category === 'free') return 'Free';
    if (activity.price_min === activity.price_max) return `${activity.price_min}`;
    if (activity.price_min && activity.price_max) return `${activity.price_min}-${activity.price_max}`;
    return activity.cost_category;
  };

  const formatDuration = (duration: string) => {
    if (duration.includes('min')) {
      const minutes = parseInt(duration);
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60);
        const remainingMins = minutes % 60;
        if (remainingMins === 0) {
          return `${hours} hr${hours > 1 ? 's' : ''}`;
        } else {
          return `${hours}h ${remainingMins}m`;
        }
      }
    }
    return duration;
  };

  const getCapacityStatus = (activity: Activity) => {
    if (!activity.capacity || !activity.current_capacity) return null;
    
    const percentage = (activity.current_capacity / activity.capacity) * 100;
    
    if (percentage >= 90) return { status: 'very_busy', color: 'bg-red-500', text: 'Very Busy' };
    if (percentage >= 70) return { status: 'busy', color: 'bg-orange-500', text: 'Busy' };
    if (percentage >= 40) return { status: 'moderate', color: 'bg-yellow-500', text: 'Moderate' };
    return { status: 'available', color: 'bg-green-500', text: 'Available' };
  };

  const WeatherWidget = () => {
    if (!weatherData) return null;
    
    return (
      <div className="bg-blue-100 p-3 rounded-lg mb-4">
        <div className="flex items-center gap-2 text-sm">
          <span>🌤️</span>
          <span>{weatherData.temperature_high}°F, {weatherData.weather_condition}</span>
          {weatherData.precipitation_chance > 30 && (
            <span className="text-blue-600">🌧️ {weatherData.precipitation_chance}% rain</span>
          )}
        </div>
      </div>
    );
  };

  const ActivityCard = ({ activity }: { activity: Activity }) => {
    const capacityStatus = getCapacityStatus(activity);
    const isFavorite = favorites.includes(activity.id);
    
    return (
      <div 
        className="bg-yellow-400 p-4 rounded-2xl cursor-pointer hover:bg-yellow-300 transition-colors"
        onClick={() => {
          setSelectedActivity(activity);
          trackActivityView(activity.id);
        }}
      >
        {/* Activity Image */}
        {activity.image_url && (
          <div className="w-full h-32 bg-gray-200 rounded-lg mb-3 overflow-hidden">
            <img 
              src={activity.image_url} 
              alt={activity.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          </div>
        )}
        
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-bold text-black text-lg flex-1">{activity.title}</h3>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              toggleFavorite(activity.id);
            }}
            className={`p-2 rounded-full ${isFavorite ? 'bg-red-500 text-white' : 'bg-black text-yellow-400'}`}
          >
            {isFavorite ? '❤️' : '⭐'}
          </button>
        </div>
        
        <p className="text-black text-sm mb-3">{activity.description}</p>
        
        {/* Timing and Pricing */}
        <div className="flex justify-between items-center mb-2">
          <div className="text-black text-xs">{formatDuration(activity.duration)}</div>
          <div className="text-black text-xs font-medium">{formatPrice(activity)}</div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex gap-2 mb-2">
          {activity.start_time && (
            <span className="bg-blue-500 text-white px-2 py-1 rounded text-xs">
              🕐 {new Date(activity.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </span>
          )}
          
          {capacityStatus && (
            <span className={`${capacityStatus.color} text-white px-2 py-1 rounded text-xs`}>
              {capacityStatus.text}
            </span>
          )}
          
          {activity.estimated_wait_time && activity.estimated_wait_time > 0 && (
            <span className="bg-orange-500 text-white px-2 py-1 rounded text-xs">
              ⏱️ {activity.estimated_wait_time}min wait
            </span>
          )}
          
          {activity.demand_level === 'high' && (
            <span className="bg-red-500 text-white px-2 py-1 rounded text-xs">
              🔥 Popular
            </span>
          )}
        </div>

        {/* Venue Info */}
        {activity.venue_name && (
          <div className="text-black text-xs mb-2">
            📍 {activity.venue_name}
            {activity.city && ` • ${activity.city}`}
          </div>
        )}
        
        {/* Tags */}
        {activity.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {activity.tags.slice(0, 4).map((tag, idx) => (
              <span key={idx} className="text-xs text-black bg-black bg-opacity-10 px-2 py-1 rounded">
                {tag}
              </span>
            ))}
            {activity.tags.length > 4 && (
              <span className="text-xs text-black">+{activity.tags.length - 4} more</span>
            )}
          </div>
        )}
        
        {/* Rating and Reviews */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <span key={i} className={`text-xs ${i < Math.floor(activity.rating) ? '⭐' : '☆'}`}>
                  {i < Math.floor(activity.rating) ? '⭐' : '☆'}
                </span>
              ))}
            </div>
            <span className="text-black text-xs">({activity.rating})</span>
            {activity.reviews && activity.reviews.length > 0 && (
              <span className="text-black text-xs">• {activity.reviews.length} reviews</span>
            )}
          </div>
          
          {activity.popularity_score && activity.popularity_score > 20 && (
            <span className="text-xs text-black bg-green-500 bg-opacity-20 px-2 py-1 rounded">
              🔥 Trending
            </span>
          )}
        </div>
      </div>
    );
  };

  if (currentScreen === 'results') {
    return (
      <div className="min-h-screen bg-white p-4 max-w-sm mx-auto">
        {/* Header */}
        <div className="flex gap-4 mb-4">
          <div className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm">
            📍 {selectedLocation}
          </div>
          <div className="bg-red-500 text-white px-4 py-2 rounded-full text-sm">
            🕐 {selectedDuration}
          </div>
        </div>

        {/* Weather Widget */}
        <WeatherWidget />

        {/* Sort and View Options */}
        <div className="flex justify-between items-center mb-4">
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="rating">Best Rated</option>
            <option value="popularity">Most Popular</option>
            <option value="price">Price: Low to High</option>
            <option value="distance">Nearest</option>
          </select>
          
          <div className="flex gap-1">
            {['grid', 'list', 'map'].map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode as any)}
                className={`px-2 py-1 text-xs rounded ${
                  viewMode === mode ? 'bg-blue-500 text-white' : 'bg-gray-200'
                }`}
              >
                {mode === 'grid' ? '⊞' : mode === 'list' ? '☰' : '🗺️'}
              </button>
            ))}
          </div>
        </div>

        {/* Active Filters */}
        {selectedFilters.length > 0 && (
          <div className="flex gap-2 mb-4 flex-wrap">
            {selectedFilters.map((filter) => (
              <span key={filter} className="bg-yellow-400 text-black px-3 py-1 rounded-full text-xs font-medium">
                {filter}
              </span>
            ))}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-gray-600">Finding perfect activities...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <div className="font-bold">Connection Error</div>
            <div className="text-sm">{error}</div>
          </div>
        )}

        {/* Activity Results */}
        {activities.length > 0 ? (
          <div className="space-y-4">
            {activities.map((activity) => (
              <ActivityCard key={activity.id} activity={activity} />
            ))}
          </div>
        ) : !loading && (
          <div className="text-center py-8">
            <div className="text-gray-600">No activities found for your criteria.</div>
            <div className="text-sm text-gray-500 mt-2">Try adjusting your filters or location.</div>
          </div>
        )}

        {/* Back Button */}
        <button
          onClick={() => setCurrentScreen('main')}
          className="w-full bg-black text-white py-3 rounded-full mt-6 font-medium"
        >
          New Search
        </button>
      </div>
    );
  }

  if (currentScreen === 'location') {
    return (
      <div className="min-h-screen bg-white p-6 max-w-sm mx-auto">
        <div className="flex items-center mb-8">
          <button onClick={() => setCurrentScreen('main')} className="text-2xl mr-4">←</button>
          <h2 className="text-2xl font-bold">Select Location</h2>
        </div>
        
        <div className="space-y-3">
          {cityOptions.map((city) => (
            <button
              key={city}
              onClick={() => {
                setSelectedLocation(city);
                setCurrentScreen('main');
                fetchWeatherData();
              }}
              className={`w-full p-5 rounded-2xl border-2 text-left font-medium transition-all ${
                selectedLocation === city
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-lg">{city}</span>
                {selectedLocation === city && <span className="text-blue-500">✓</span>}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (currentScreen === 'duration') {
    return (
      <div className="min-h-screen bg-white p-6 max-w-sm mx-auto">
        <div className="flex items-center mb-8">
          <button onClick={() => setCurrentScreen('main')} className="text-2xl mr-4">←</button>
          <h2 className="text-2xl font-bold">How long do you have?</h2>
        </div>
        
        <div className="space-y-3">
          {durationOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                setSelectedDuration(option.value);
                setCurrentScreen('main');
              }}
              className={`w-full p-5 rounded-2xl border-2 text-left font-medium transition-all ${
                selectedDuration === option.value
                  ? 'border-red-500 bg-red-50 text-red-700'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg">{option.label}</div>
                  <div className="text-sm text-gray-500">
                    {option.category === 'quick' && 'Perfect for a quick visit'}
                    {option.category === 'short' && 'Great for focused activities'}
                    {option.category === 'medium' && 'Explore at a comfortable pace'}
                    {option.category === 'long' && 'Plenty of time to enjoy'}
                    {option.category === 'full_day' && 'Make it a full adventure'}
                  </div>
                </div>
                {selectedDuration === option.value && <span className="text-red-500">✓</span>}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Main screen - Updated to match Figma design
  return (
    <div className="min-h-screen bg-white p-6 max-w-sm mx-auto">
      {/* Header matching Figma */}
      <div className="flex justify-between items-center mb-8">
        <div className="text-2xl font-bold text-black">TOT TROT</div>
        <div className="flex gap-4">
          <button className="text-2xl">📍</button>
          <button className="text-2xl">☰</button>
        </div>
      </div>

      {/* Weather Widget */}
      <WeatherWidget />

      {/* Benny Name Display (matching Figma) */}
      <div className="mb-6">
        <div className="bg-green-500 text-white px-8 py-4 rounded-full text-center">
          <span className="text-lg font-semibold">Benny</span>
        </div>
      </div>

      {/* Location Selector (matching Figma blue pill) */}
      <div className="mb-4">
        <div className="bg-blue-500 text-white px-8 py-4 rounded-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>📍</span>
            <span className="text-lg font-medium">{selectedLocation}</span>
          </div>
          <button 
            className="text-sm bg-blue-400 px-4 py-2 rounded-full hover:bg-blue-300 transition-colors"
            onClick={() => setCurrentScreen('location')}
          >
            CHANGE
          </button>
        </div>
      </div>

      {/* Duration Selector (matching Figma red pill) */}
      <div className="mb-8">
        <div className="bg-red-500 text-white px-8 py-4 rounded-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>🕐</span>
            <span className="text-lg font-medium">{selectedDuration}</span>
          </div>
          <button 
            className="text-sm bg-red-400 px-4 py-2 rounded-full hover:bg-red-300 transition-colors"
            onClick={() => setCurrentScreen('duration')}
          >
            CHANGE
          </button>
        </div>
      </div>

      {/* Filter Section (matching Figma yellow card) */}
      <div className="bg-yellow-400 p-6 rounded-3xl mb-8">
        <div className="text-black font-bold text-2xl mb-6">Find something</div>
        
        <div className="flex flex-wrap gap-3 mb-6">
          {filterOptions.map((filter) => (
            <button
              key={filter}
              onClick={() => toggleFilter(filter)}
              className={`px-5 py-3 rounded-full text-sm font-semibold border-2 border-black transition-all ${
                selectedFilters.includes(filter)
                  ? 'bg-black text-yellow-400'
                  : 'bg-transparent text-black hover:bg-black hover:text-yellow-400'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Show "SEE ALL" button when filters selected (matching Figma) */}
        {selectedFilters.length > 0 && (
          <div className="text-center mb-4">
            <button className="text-black text-sm font-medium border-2 border-black px-6 py-2 rounded-full">
              SEE ALL
            </button>
          </div>
        )}
      </div>

      {/* Go Button (matching Figma black pill) */}
      <button
        onClick={handleSearch}
        disabled={loading}
        className={`w-full py-5 rounded-full text-2xl font-bold transition-all ${
          loading 
            ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
            : 'bg-black text-white hover:bg-gray-800'
        }`}
      >
        {loading ? 'Searching...' : 'Go'}
      </button>

      {/* Quick Actions - Modern styling */}
      <div className="mt-8 grid grid-cols-2 gap-4">
        <button 
          onClick={() => {
            setSelectedFilters(['HAPPENING NOW']);
            handleSearch();
          }}
          className="bg-green-500 text-white py-4 rounded-2xl text-sm font-semibold hover:bg-green-600 transition-colors"
        >
          🔴 Live Events
        </button>
        <button 
          onClick={() => {
            setSelectedFilters(['FREE']);
            handleSearch();
          }}
          className="bg-blue-500 text-white py-4 rounded-2xl text-sm font-semibold hover:bg-blue-600 transition-colors"
        >
          💰 Free Activities
        </button>
      </div>

      {/* Status indicator */}
      <div className="mt-6 text-center">
        <div className="text-xs text-gray-400">
          Updated with {activities.length || 'latest'} activities • {new Date().toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}

export default App;
