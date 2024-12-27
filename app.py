from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from geolocator.geolocator import nearby_hospitals
import math
import requests

cred = credentials.Certificate("aarogyam-d06ff-firebase-adminsdk-cwxbv-f009afdfb4.json")
firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

app = Flask(__name__)
CORS(app)

# Signup Endpoint
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password or not name:
            error = "Missing email, password, or name"
            return render_template('signup.html', error=error)

        try:
            # Store user details in Firestore
            user_ref = db.collection('users').document(email)
            user_ref.set({
                'email': email,
                'password': password,  # Not recommended to store passwords in plaintext; hash them
                'name': name,
            })
            return redirect(url_for('signin'))
        except Exception as e:
            error = f"Error: {str(e)}"
            return render_template('signup.html', error=error)

    return render_template('signup.html')

# Signin Endpoint
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            error = "Missing email or password"
            return render_template('login.html', error=error)

        try:
            # Retrieve user details from Firestore
            user_ref = db.collection('users').document(email)
            user_doc = user_ref.get()

            if not user_doc.exists:
                error = "User does not exist"
                return render_template('login.html', error=error)

            user_data = user_doc.to_dict()
            if user_data['password'] != password:  # Again, use hashed passwords in production
                error = "Invalid credentials"
                return render_template('login.html', error=error)

            return render_template('welcome.html', user=user_data)
        except Exception as e:
            error = f"Error: {str(e)}"
            return render_template('login.html', error=error)

    return render_template('login.html')

# Register Result
@app.route('/register_result', methods=['POST'])
def register_result():
    data = request.json
    email = data.get('email')
    result = data.get('result')

    if not email or not result:
        return "Missing email or result", 400

    try:
        # Save result to Firestore
        result_ref = db.collection('results').document()
        result_ref.set({
            'email': email,
            'result': result
        })
        return "Result registered successfully", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

# Fetch Results
@app.route('/get_results/<email>', methods=['GET'])
def get_results(email):
    try:
        # Fetch user results from Firestore
        results_ref = db.collection('results').where('email', '==', email).stream()
        results = [doc.to_dict() for doc in results_ref]
        return render_template('results.html', results=results)
    except Exception as e:
        return f"Error: {str(e)}", 500

def cartesian_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def get_userlocation():
    res = requests.get('http://ip-api.com/json/')
    if res.status_code == 200:
        data = res.json()
        lat = data.get('lat')
        long = data.get('lon')
        return lat, long
    
@app.route('/nearby_hospitals', methods = ['GET'])
def nearest_hospitals():
    try:
        lat, long = get_userlocation()
        
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
            hospital["distance"] = cartesian_distance(lat, long, hospital["lat"], hospital["long"])
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


if __name__ == "__main__":
    app.run(debug=True)
