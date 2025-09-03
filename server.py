from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import math

app = Flask(__name__)
CORS(app)

# In-memory database jo simulator se live bus data store karta hai
bus_data = {}

# === MASTER DATA (Asli Duniya jaisa Data) ===
CITIES = {
    'chandigarh': {'lat': 30.7333, 'lng': 76.7794, 'name': 'Chandigarh ISBT'},
    'gurgaon':    {'lat': 28.4595, 'lng': 77.0266, 'name': 'Gurgaon ISBT'},
    'ambala':     {'lat': 30.3782, 'lng': 76.7767, 'name': 'Ambala Cantt'},
    'hisar':      {'lat': 29.1492, 'lng': 75.7217, 'name': 'Hisar ISBT'},
    'rohtak':     {'lat': 28.8955, 'lng': 76.6066, 'name': 'Rohtak ISBT'},
    'faridabad':  {'lat': 28.4089, 'lng': 77.3178, 'name': 'Faridabad ISBT'},
    'karnal':     {'lat': 29.6857, 'lng': 76.9905, 'name': 'Karnal'},
    'sonipat':    {'lat': 28.9931, 'lng': 77.0151, 'name': 'Sonipat'},
    'panipat':    {'lat': 29.3909, 'lng': 76.9635, 'name': 'Panipat'},
    'delhi':      {'lat': 28.6667, 'lng': 77.2167, 'name': 'Delhi ISBT'},
    'sirsa':      {'lat': 29.5372, 'lng': 75.0234, 'name': 'Sirsa ISBT'},
    'jhajjar':    {'lat': 28.6101, 'lng': 76.6573, 'name': 'Jhajjar'},
    'fatehabad':  {'lat': 29.5147, 'lng': 75.4522, 'name': 'Fatehabad'}
}
DETAILED_ROUTES = {
    'chandigarh-gurgaon': [ CITIES['chandigarh'], CITIES['ambala'], CITIES['karnal'], CITIES['panipat'], CITIES['sonipat'], CITIES['gurgaon'] ],
    'hisar-sirsa':        [ CITIES['hisar'], CITIES['fatehabad'], CITIES['sirsa'] ],
    'rohtak-faridabad':   [ CITIES['rohtak'], CITIES['jhajjar'], CITIES['gurgaon'], CITIES['faridabad'] ],
    'ambala-delhi':       [ CITIES['ambala'], CITIES['karnal'], CITIES['panipat'], CITIES['delhi'] ],
    'hisar-gurgaon':      [ CITIES['hisar'], CITIES['rohtak'], CITIES['jhajjar'], CITIES['gurgaon'] ]
}
BUS_STAND_INFO = {
    'chandigarh': { 'facilities': 'AC Waiting Room, Food Court, Cloak Room', 'routes': ['Gurgaon', 'Delhi', 'Hisar'] },
    'gurgaon':    { 'facilities': 'Metro Connectivity, Food Stalls, Washrooms', 'routes': ['Chandigarh', 'Jaipur', 'Faridabad'] },
    'hisar':      { 'facilities': 'Waiting Hall, Book Stall, Local Bus Service', 'routes': ['Sirsa', 'Chandigarh', 'Delhi'] },
    'rohtak':     { 'facilities': 'Medical Room, Police Booth, Food Court', 'routes': ['Faridabad', 'Hisar', 'Delhi'] },
}

ALL_ROUTES = {}
for key, stops in DETAILED_ROUTES.items():
    start_city, end_city = key.split('-')
    ALL_ROUTES[key] = {'stops': stops}
    reverse_key = f"{end_city}-{start_city}"
    ALL_ROUTES[reverse_key] = {'stops': stops[::-1]}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_fare_logic(distance_km):
    fares = {'Ordinary': distance_km * 1.25, 'AC Express': distance_km * 1.75, 'Volvo': distance_km * 2.50}
    return {k: round(v, 2) for k, v in fares.items()}

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    bus_id = data.get('id')
    if not bus_id: return jsonify({'error': 'Missing bus id'}), 400
    bus_data[bus_id] = { **data, 'last_updated': datetime.utcnow().isoformat() + 'Z' }
    return jsonify({'message': f'Location updated for bus {bus_id}'}), 200

@app.route('/get_live_buses')
def get_live_buses():
    return jsonify(list(bus_data.values()))

@app.route('/get_route_details')
def get_route_details():
    start, end = request.args.get('start', '').lower(), request.args.get('end', '').lower()
    key = f"{start}-{end}"
    if key not in ALL_ROUTES: return jsonify({'error': f'Route not defined.'}), 404
    return jsonify(ALL_ROUTES[key])

@app.route('/find_nearby_stops')
def find_nearby_stops():
    try:
        user_lat, user_lon = float(request.args.get('lat')), float(request.args.get('lon'))
    except (TypeError, ValueError): return jsonify({'error': 'Invalid latitude/longitude'}), 400
    stops_with_distance = [{**city_data, 'id': key, 'distance_km': haversine(user_lat, user_lon, city_data['lat'], city_data['lng'])} for key, city_data in CITIES.items()]
    return jsonify(sorted(stops_with_distance, key=lambda x: x['distance_km'])[:5])

@app.route('/calculate_fare')
def calculate_fare():
    start, end = request.args.get('start', '').lower(), request.args.get('end', '').lower()
    if not start or not end or start not in CITIES or end not in CITIES: return jsonify({'error': 'Invalid city names'}), 400
    start_city, end_city = CITIES[start], CITIES[end]
    distance = haversine(start_city['lat'], start_city['lng'], end_city['lat'], end_city['lng'])
    fares = calculate_fare_logic(distance)
    return jsonify({'distance_km': round(distance), 'fares': fares})

@app.route('/get_bus_stand_details')
def get_bus_stand_details():
    city = request.args.get('city', '').lower()
    if not city or city not in CITIES: return jsonify({'error': 'Invalid city name'}), 400
    info = BUS_STAND_INFO.get(city, { 'facilities': 'Basic amenities available.', 'routes': ['Local and long-distance routes.'] })
    return jsonify({**CITIES[city], **info})

if __name__ == '__main__':
    print("Super Smart Flask server is running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1')

