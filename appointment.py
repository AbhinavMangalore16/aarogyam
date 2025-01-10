import requests
import os
from dotenv import load_dotenv

load_dotenv()

ZODOC_API_URL = os.environ['ZODOC_API_URL']
ZODOC_API_KEY = os.environ["ZODOC_API_KEY"]

def get_available_slots(provider_id, date):
    url = f"{ZODOC_API_URL}/appointments/{provider_id}/available-slots"
    headers = {"Authorization": f"Bearer {ZODOC_API_KEY}"}
    params = {"date": date}

    response = requests.get(url, headers=headers, params=params)
    return response.json()

def book_appointment(provider_id, slot_id, user_details):
    url = f"{ZODOC_API_URL}/appointments/book"
    headers = {"Authorization": f"Bearer {ZODOC_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "provider_id": provider_id,
        "slot_id": slot_id,
        "user_details": user_details
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def reschedule_appointment(appointment_id, new_slot_id):
    url = f"{ZODOC_API_URL}/appointments/{appointment_id}/reschedule"
    headers = {"Authorization": f"Bearer {ZODOC_API_KEY}", "Content-Type": "application/json"}
    payload = {"new_slot_id": new_slot_id}

    response = requests.put(url, headers=headers, json=payload)
    return response.json()

def cancel_appointment(appointment_id):
    url = f"{ZODOC_API_URL}/appointments/{appointment_id}/cancel"
    headers = {"Authorization": f"Bearer {ZODOC_API_KEY}"}

    response = requests.delete(url, headers=headers)
    return response.json()
