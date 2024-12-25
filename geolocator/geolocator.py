from flask import Flask, request, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

load_dotenv()
NOMINATIM = os.getenv("NOMINATIM_API_URL")
OVERPASS = os.getenv("OVERPASS_API_URL")

if not NOMINATIM or not OVERPASS:
    raise EnvironmentError("NOMINATIM_API_URL and OVERPASS_API_URL must be set in the .env file")

def nearby_hospitals(lat, long):
    OVERPASS_API_URL = f"{OVERPASS}"
    query = f"""
    [out:json];
    node["amenity"="hospital"](around:5000,{lat},{long});
    out;
    """
    try:
        response = requests.get(OVERPASS_API_URL, params={'data': query})
        response.raise_for_status()
        data = response.json()
        hospitals = []
        for hospital in data.get("elements", []):
            hospitals.append({
                "name": hospital.get("tags", {}).get("name", "unknown"),
                "latitude": hospital.get("lat"),
                "longitude": hospital.get("lon"),
                "address": hospital.get("tags", {}).get("addr:full", "Not available"),
                "vicinity": hospital.get("vicinity"),
                "rating": hospital.get("rating", "N/A"),
                "contact": hospital.get("formatted_phone_number", "N/A")
            })
        return hospitals
    except requests.RequestException as e:
        return {"error": f"request failed: {str(e)}"}