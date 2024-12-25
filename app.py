from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from geolocator.geolocator import nearby_hospitals

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

@app.route('/hosps_nearby', methods=['GET'])
def fetch_hospitals():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    if not (latitude and longitude):
        return {"error": "latitude and longitude are required"}, 400
    hospitals = nearby_hospitals(latitude, longitude)
    return jsonify(hospitals)





if __name__ == "__main__":
    app.run(debug=True)
