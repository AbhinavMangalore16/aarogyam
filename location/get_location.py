import requests
import math
import os

def cartesian_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def get_userlocation():
    res = requests.get(os.environ['LOCATION_URI'])
    if res.status_code == 200:
        data = res.json()
        lat = data.get('lat')
        long = data.get('lon')
        return lat, long