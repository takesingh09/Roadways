import requests
import time
import random
import math

# Yeh aapke Flask server ka address hai jahan data bhejna hai
API_URL = "http://127.0.0.1:5000/update_location"

# Simulator ke liye routes aur unke stops ki master list
SIMULATOR_ROUTES = {
    'chandigarh-gurgaon': [ {'name': 'Chandigarh ISBT', 'lat': 30.7333, 'lng': 76.7794}, {'name': 'Ambala Cantt', 'lat': 30.3782, 'lng': 76.7767}, {'name': 'Karnal', 'lat': 29.6857, 'lng': 76.9905}, {'name': 'Panipat', 'lat': 29.3909, 'lng': 76.9635}, {'name': 'Sonipat', 'lat': 28.9931, 'lng': 77.0151}, {'name': 'Gurgaon ISBT', 'lat': 28.4595, 'lng': 77.0266} ],
    'hisar-sirsa': [ {'name': 'Hisar ISBT', 'lat': 29.1492, 'lng': 75.7217}, {'name': 'Fatehabad', 'lat': 29.5147, 'lng': 75.4522}, {'name': 'Sirsa ISBT', 'lat': 29.5372, 'lng': 75.0234} ],
    'rohtak-faridabad': [ {'name': 'Rohtak ISBT', 'lat': 28.8955, 'lng': 76.6066}, {'name': 'Jhajjar', 'lat': 28.6101, 'lng': 76.6573}, {'name': 'Gurgaon ISBT', 'lat': 28.4595, 'lng': 77.0266}, {'name': 'Faridabad ISBT', 'lat': 28.4089, 'lng': 77.3178} ],
    'ambala-delhi': [ {'name': 'Ambala Cantt', 'lat': 30.3782, 'lng': 76.7767}, {'name': 'Karnal', 'lat': 29.6857, 'lng': 76.9905}, {'name': 'Panipat', 'lat': 29.3909, 'lng': 76.9635}, {'name': 'Delhi ISBT', 'lat': 28.6667, 'lng': 77.2167} ],
    'hisar-gurgaon': [ {'name': 'Hisar ISBT', 'lat': 29.1492, 'lng': 75.7217}, {'name': 'Rohtak ISBT', 'lat': 28.8955, 'lng': 76.6066}, {'name': 'Jhajjar', 'lat': 28.6101, 'lng': 76.6573}, {'name': 'Gurgaon ISBT', 'lat': 28.4595, 'lng': 77.0266} ]
}

class Bus:
    """Ek bus object jo apni position, type, aur seat status ko manage aur update karta hai."""
    def __init__(self, bus_id, number, route_key):
        self.id = bus_id
        self.number = number
        self.routeKey = route_key
        self.route = SIMULATOR_ROUTES[self.routeKey]
        self.segment_index = random.randint(0, len(self.route) - 2)
        self.segment_progress = random.random()
        self.status = "On Time" if random.random() > 0.2 else "Delayed"
        self.bearing = 0
        self.bus_type = random.choice(['Ordinary', 'AC Express', 'Volvo'])
        self.seat_status = random.choice(['Seats Available', 'Filling Fast', 'Full'])

    def update_position(self):
        """Bus ko route par aage badhata hai aur server ke liye data packet return karta hai."""
        self.segment_progress += 0.05 # Speed of the bus
        
        if self.segment_progress >= 1.0:
            self.segment_progress = 0.0
            self.segment_index = (self.segment_index + 1) % (len(self.route) - 1)
            # Har stop ke baad seat status badalne ka chance
            if random.random() > 0.5:
                 self.seat_status = random.choice(['Seats Available', 'Filling Fast', 'Full'])

        start_point = self.route[self.segment_index]
        end_point = self.route[self.segment_index + 1]

        lat = start_point['lat'] + (end_point['lat'] - start_point['lat']) * self.segment_progress
        lon = start_point['lng'] + (end_point['lng'] - start_point['lng']) * self.segment_progress
        
        dLon = end_point['lng'] - start_point['lng']
        y = math.sin(math.radians(dLon)) * math.cos(math.radians(end_point['lat']))
        x = math.cos(math.radians(start_point['lat'])) * math.sin(math.radians(end_point['lat'])) - \
            math.sin(math.radians(start_point['lat'])) * math.cos(math.radians(end_point['lat'])) * math.cos(math.radians(dLon))
        self.bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

        return {
            "id": self.id,
            "number": self.number,
            "latitude": lat,
            "longitude": lon,
            "status": self.status,
            "routeKey": self.routeKey,
            "bearing": self.bearing,
            "next_stop": end_point,
            "bus_type": self.bus_type,
            "seat_status": self.seat_status,
            "route": self.route # Poora route bhi bhejo taaki Dynamic ETA me kaam aaye
        }

# === GUARANTEED BUSES ON ROUTES ===
fleet = []
bus_counter = 0

for route_key in list(SIMULATOR_ROUTES.keys()):
    start, end = route_key.split('-')
    reverse_route_key = f"{end}-{start}"
    
    if reverse_route_key not in SIMULATOR_ROUTES:
        SIMULATOR_ROUTES[reverse_route_key] = SIMULATOR_ROUTES[route_key][::-1]

    # Har route par kam se kam 3 bus daalo
    for i in range(3):
        fleet.append(Bus(f"HR-BUS-{bus_counter}", f"HR{55+bus_counter//26}{chr(65+bus_counter%26)}-{1000+bus_counter*12}", route_key))
        bus_counter += 1
    # Har reverse route par bhi 3 bus daalo
    for i in range(3):
        fleet.append(Bus(f"HR-BUS-{bus_counter}", f"HR{55+bus_counter//26}{chr(65+bus_counter%26)}-{1000+bus_counter*12}", reverse_route_key))
        bus_counter += 1

print(f"Realistic Bus Simulator is running with {len(fleet)} buses...")
print("This script is sending live, realistic data to your Flask server.")
print("Press Ctrl+C to stop.")

while True:
    for bus in fleet:
        location_data = bus.update_position()
        try:
            requests.post(API_URL, json=location_data, timeout=2)
        except requests.exceptions.RequestException:
            pass 
    
    time.sleep(3)

