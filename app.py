from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import uuid
from functools import wraps
import os

cred = credentials.Certificate("aarogyam-d06ff-firebase-adminsdk-cwxbv-f009afdfb4.json")
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

@app.route('/register_result', methods=['POST'])
@jwt_authenticate
def register_result():
    data = request.json
    email = data.get('email')
    result = data.get('result')

    if not email or not result:
        return jsonify({'message': 'Missing email or result'}), 400

    try:
        result_ref = db.collection('results').document()
        result_ref.set({
            'email': email,
            'result': result
        })
        return jsonify({'message': 'Result registered successfully'}), 201
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/get_results/<email>', methods=['GET'])
@jwt_authenticate
def get_results(email):
    try:
        results_ref = db.collection('results').where('email', '==', email).stream()
        results = [doc.to_dict() for doc in results_ref]
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True)
