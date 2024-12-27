import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request
import requests
from ..app import app


db = firestore.client()

lat = 37.7749
long = 85.0232

def get_userlocation():
    res = requests.get('http://ip-api.com/json/')
    if res.status_code == 200:
        data = res.json()
        lat = data.get('lat')
        long = data.get('lon')
        return lat, long

def save_location(lat, long):
    try:
        collection_ref = db.collection('random_testing')

        doc = collection_ref.add({
            "lat": lat,
            "long": long
        })

        print(f"document added: {doc[1].id}")
    except Exception as e:
        print(f"Error: {str(e)}")



lat, long = get_userlocation()         
save_location(lat, long)