from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import uuid
from functools import wraps
import os
from location import get_location

cred = credentials.Certificate(os.environ['FIREBASE_KEY'])
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['APP_KEY']

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
def get_all_hospitals():
    try:
        hospitals_ref = db.collection('hospitals').stream()
        results = [doc.to_dict() for doc in hospitals_ref]
        return results, 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
