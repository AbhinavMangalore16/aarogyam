from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import datetime
import uuid
from functools import wraps
import os
from location import get_location
from format_files import format_records, format_individual_resource
import requests
from appointment import get_available_slots, book_appointment, reschedule_appointment, cancel_appointment

cred = credentials.Certificate(os.environ['FIREBASE_KEY'])
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['APP_KEY']

practitioners_ref = db.collection('practitioners')
appointments_ref = db.collection('appointments')

def jwt_authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.collection('users').document(data['email']).get()
            if not current_user.exists:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

def check_practitioner_exists(provider_id):
    practitioner = practitioners_ref.where("id", "==", provider_id).get()
    return len(practitioner) > 0

def fetch_slots(provider_id):
    # Fetch all appointments for the given provider
    booked_appointments = appointments_ref.where("provider_id", "==", provider_id).stream()

    # Collect booked slots
    booked_slots = {(appt.to_dict().get("date"), appt.to_dict().get("time")) for appt in booked_appointments}

    # Generate default slots (e.g., next 7 days, 9 AM - 5 PM)
    today = datetime.now()
    available_slots = []
    for day_offset in range(7):  # Next 7 days
        current_date = (today + timedelta(days=day_offset)).date().isoformat()
        for hour in range(9, 17):  # 9 AM to 5 PM
            time = f"{hour}:00"
            if (current_date, time) not in booked_slots:
                available_slots.append({"date": current_date, "time": time})

    return available_slots

def update_slot_availability(provider_id, slot_id, is_available):
    slot_ref = practitioners_ref.document(provider_id).collection('slots').document(slot_id)
    slot = slot_ref.get()
    if not slot.exists:
        return False
    slot_ref.update({"is_available": is_available})
    return True

def fetch_slots(provider_id):
    slots_ref = practitioners_ref.document(provider_id).collection('slots')
    slots_docs = slots_ref.where("is_available", "==", True).get()

    # Convert the Firestore documents to a list of slot dictionaries
    slots = [{"slot_id": doc.id, "time": doc.to_dict().get("time")} for doc in slots_docs]
    return slots

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({'message': 'Missing email, password, or name'}), 400

    try:
        user_ref = db.collection('users').document(email)
        if user_ref.get().exists:
            return jsonify({'message': 'User already exists'}), 400

        hashed_password = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        user_ref.set({
            'email': email,
            'password': hashed_password,
            'name': name,
            'user_id': user_id
        })
        return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing email or password'}), 400

    try:
        user_ref = db.collection('users').document(email)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'message': 'User does not exist'}), 404

        user_data = user_doc.to_dict()
        if not check_password_hash(user_data['password'], password):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = jwt.encode({
            'email': email,
            'user_id': user_data['user_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
    
@app.route('/nearby_hospitals', methods = ['GET'])
@jwt_authenticate
def nearest_hospitals():
    try:
        lat, long = get_location.get_userlocation()
        
        hospitals_ref = db.collection('hospitals')
        for doc in hospitals_ref.stream():
            print(doc.to_dict())
        hospitals = [
            {
                "uuid": doc.get("uuid"),
                "name": doc.get("name"),
                "lat": float(doc.get("lat")),
                "long": float(doc.get("long")),
                
            }
            for doc in hospitals_ref.stream()
        ]

        for hospital in hospitals:
            hospital["distance"] = get_location.cartesian_distance(lat, long, hospital["lat"], hospital["long"])
        nearest_hosps = sorted(hospitals, key=lambda x: x["distance"])[:3]
        return jsonify({
            "nearest_hospitals": [
                {
                    "uuid": hospital["uuid"],
                    "name": hospital["name"],
                    "latitude": hospital["lat"],
                    "longitude": hospital["long"],
                }
                for hospital in nearest_hosps
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/register_hospital', methods=['GET','POST'])
@jwt_authenticate
def register_hospital():
    if request.method=="POST":
        data = request.form
        name = data.get('name')
        lat = data.get('latitude')
        long = data.get('longitude')

        errors = {
            not name: "Name is missing",
            not lat: "Latitude is missing",
            not long: "Longitude is missing"
        }

        for condition, message in errors.items():
            if condition:
                return {'message': message}, 400
        
        try:
            hospital_ref = db.collection("hospitals").document()
            hospital_ref.set({
                'uuid': str(uuid.uuid4()),
                'name':name,
                'lat':lat,
                'long':long

            })
            return "Result registered successfully", 200
        except Exception as e:
            return f"Error: {str(e)}", 500

@app.route('/get_hospitals', methods=['GET'])
@jwt_authenticate
def get_all_hospitals():
    try:
        hospitals_ref = db.collection('hospitals').stream()
        results = [doc.to_dict() for doc in hospitals_ref]
        return results, 200
    except Exception as e:
        return f"Error: {str(e)}", 500
    
@app.route('/add_user', methods = ['GET','POST'])
@jwt_authenticate
def add_user(user_id, name, email):
    user_ref = db.collection('user-test1').document(user_id)
    user_ref.set({
        "name": name, 
        "email": email
    })
    print(f"User {name} added successfully..")

@app.route('/add_health_rec', methods = ['POST'])
@jwt_authenticate
def add_health_rec():
    try:
        data = request.json
        user_id = data.get('user_id')
        record_data = data.get('record_data')
        print(user_id, record_data)
        if not user_id or not record_data:
            return jsonify({'message': 'Missing user_id or record_data'}), 400
        record_ref = db.collection("user-test1").document(user_id).collection("healthRecords").document()
        record_data["id"] = record_ref.id
        record_ref.set(record_data)
        return jsonify({'message': f'Health record with ID {record_ref.id} added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_health_rec/<user_Id>', methods=['GET'])
@jwt_authenticate
def get_health_rec(user_Id):
    try:
        if not user_Id:
            return jsonify({'message': 'Missing user_id'}), 400
        
        # Get the optional record type from query params
        record_type = request.args.get('type')
        valid_types = ['Patient', 'Observation', 'Condition', 'Medication', 'Encounter']  # Add other types if needed
        
        if record_type and record_type not in valid_types:
            return jsonify({'message': f'Invalid record type: {record_type}. Valid types are: {", ".join(valid_types)}'}), 400

        # Retrieve health records from Firestore
        records_ref = db.collection("user-test1").document(user_Id).collection("healthRecords")
        docs = records_ref.stream()
        records = [doc.to_dict() for doc in docs]

        if not records:
            return jsonify({'message': 'No records found for this user'}), 404

        # Filter records if a specific type is requested
        if record_type:
            filtered_records = []
            for record in records:
                if record.get('resourceType') == 'Bundle':
                    # Filter entries within the bundle by record type
                    for entry in record.get('entry', []):
                        resource = entry.get('resource', {})
                        if resource.get('resourceType') == record_type:
                            filtered_records.append(resource)
                elif record.get('resourceType') == record_type:
                    filtered_records.append(record)

            if not filtered_records:
                return jsonify({'message': f'No records found for type: {record_type}'}), 404
            return jsonify({'records': format_records(filtered_records)}), 200

        # Format and return all records if no specific type is requested
        return jsonify({'records': format_records(records)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_resource', methods=['POST'])
@jwt_authenticate
def add_resource():
    """
    Add any FHIR resource (e.g., Patient, Practitioner, Encounter, etc.)
    """
    try:
        data = request.json
        resource_type = data.get("resourceType")
        if not resource_type:
            return jsonify({'message': 'Missing resourceType'}), 400

        # Get the collection for the resource
        collection_name = resource_type.lower() + 's'  # e.g., 'patients', 'conditions'
        resource_ref = db.collection(collection_name).document()
        data["id"] = resource_ref.id
        resource_ref.set(data)

        return jsonify({'message': f'{resource_type} added successfully', 'id': resource_ref.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_resource/<resource_type>/<resource_id>', methods=['GET'])
@jwt_authenticate
def get_resource(resource_type, resource_id):
    """
    Retrieve a specific FHIR resource by type and ID.
    """
    try:
        collection_name = resource_type.lower() + 's'  # e.g., 'patients', 'conditions'
        resource_ref = db.collection(collection_name).document(resource_id)
        resource = resource_ref.get()

        if not resource.exists:
            return jsonify({'message': f'{resource_type} not found'}), 404

        return jsonify(resource.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_resources/<resource_type>', methods=['GET'])
@jwt_authenticate
def get_resources(resource_type):
    """
    Retrieve all resources of a specific type.
    """
    try:
        collection_name = resource_type.lower() + 's'
        resources_ref = db.collection(collection_name).stream()
        resources = [doc.to_dict() for doc in resources_ref]

        if not resources:
            return jsonify({'message': f'No {resource_type} records found'}), 404

        return jsonify({'resources': resources}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/filter_resources/<resource_type>', methods=['GET'])
@jwt_authenticate
def filter_resources(resource_type):
    """
    Filter resources by a query parameter (e.g., gender, condition code, etc.)
    """
    try:
        collection_name = resource_type.lower() + 's'
        query_field = request.args.get('field')  # Field to filter by
        query_value = request.args.get('value')  # Value to match

        if not query_field or not query_value:
            return jsonify({'message': 'Missing field or value for filtering'}), 400

        resources_ref = db.collection(collection_name).where(query_field, '==', query_value).stream()
        resources = [doc.to_dict() for doc in resources_ref]

        if not resources:
            return jsonify({'message': f'No {resource_type} records match the query'}), 404

        return jsonify({'resources': resources}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_health_rec', methods=['POST'])
@jwt_authenticate
def update_health_rec():
    try:
        data = request.json
        user_id = data.get('user_id')
        record_id = data.get('record_id')
        record_data = data.get('record_data')
        if not user_id or not record_id or not record_data:
            return jsonify({'message': 'Missing required fields'}), 400
        record_ref = db.collection("user-test1").document(user_id).collection("healthRecords").document(record_id)
        record_ref.update(record_data)
        return jsonify({'message': f'Health record with ID {record_id} updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_health_rec', methods = ['DELETE'])
@jwt_authenticate
def delete_health_rec():
    try:
        user_id = request.args.get('user_id')
        record_id = request.args.get('record_id')
        if not user_id or not record_id:
            return jsonify({'message': 'Missing user_id or record_id'}), 400   
        record_ref = db.collection("user-test1").document(user_id).collection("healthRecords").document(record_id)
        record_ref.delete()
        print(f"Health record with ID: {record_id} deleted successfully..")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book', methods=['POST'])
@jwt_authenticate
def book_appointment():
    data = request.json
    provider_id = data['provider_id']
    date = data['date']
    time = data['time']

    # Extract user details from JWT
    token = request.headers.get('x-access-token')
    decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    user_email = decoded_token.get('email')
    current_user = db.collection('users').document(user_email).get()
    user_details = current_user.to_dict() if current_user.exists else {}

    if not user_details:
        return jsonify({"error": "User not found in database."}), 401

    # Check if practitioner exists
    if not check_practitioner_exists(provider_id):
        return jsonify({"error": "Invalid provider_id"}), 404

    # Check if slot is already booked
    existing_appointment = appointments_ref.where("provider_id", "==", provider_id).where("date", "==", date).where("time", "==", time).get()
    if existing_appointment:
        return jsonify({"error": "Slot already booked"}), 400

    # Book appointment
    appointment = {
        "provider_id": provider_id,
        "date": date,
        "time": time,
        "user_details": {
            "email": user_email,
            "name": user_details.get("name")
        },
        "status": "booked"
    }
    appointment_ref = appointments_ref.add(appointment)

    return jsonify({"status": "success", "appointment_id": appointment_ref[1].id})

# View Slots
@app.route('/slots/<provider_id>', methods=['GET'])
@jwt_authenticate
def get_slots(provider_id):
    # Check if practitioner exists
    if not check_practitioner_exists(provider_id):
        return jsonify({"error": "Invalid provider_id"}), 404

    # Fetch available slots
    slots = fetch_slots(provider_id)

    if not slots:
        return jsonify({"error": "No available slots found for this provider."}), 404

    return jsonify({"slots": slots})

# Reschedule Appointment
@app.route('/reschedule', methods=['POST'])
@jwt_authenticate
def reschedule_appointment():
    data = request.json
    appointment_id = data['appointment_id']
    new_date = data['new_date']
    new_time = data['new_time']

    appointment_ref = appointments_ref.document(appointment_id)
    appointment = appointment_ref.get()
    if not appointment.exists:
        return jsonify({"error": "Invalid appointment_id"}), 404

    provider_id = appointment.to_dict().get("provider_id")

    # Check if the new slot is available
    existing_appointment = appointments_ref.where("provider_id", "==", provider_id).where("date", "==", new_date).where("time", "==", new_time).get()
    if existing_appointment:
        return jsonify({"error": "New slot not available"}), 400

    # Update appointment
    appointment_ref.update({"date": new_date, "time": new_time, "status": "rescheduled"})

    return jsonify({"status": "success", "message": "Appointment rescheduled successfully."})

# Cancel Appointment
@app.route('/cancel_appointment', methods=['POST'])
@jwt_authenticate
def cancel_appointment():
    data = request.json
    appointment_id = data['appointment_id']

    appointment_ref = appointments_ref.document(appointment_id)
    appointment = appointment_ref.get()

    # Corrected the existence check
    if not appointment.exists:  # Remove parentheses
        return jsonify({"error": "Invalid appointment_id"}), 404

    # Update appointment status
    appointment_ref.update({"status": "canceled"})

    return jsonify({"status": "success", "message": "Appointment canceled successfully."})


if __name__ == "__main__":
    app.run(debug=True)