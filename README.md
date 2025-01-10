# HealthAPI Backend

This project is a Flask-based backend developed for a Postman API Hackathon hosted by BITS Pilani. It is a healthcare management system that leverages Firebase for data storage and JWT for authentication. The application supports functionalities like user authentication, hospital registration, appointment scheduling, and management of healthcare records.

---

## Features

1. **User Management**
   - **Signup**: Register new users.
   - **Signin**: Authenticate users with JWT tokens.
   - **Health Record Management**: Add, update, delete, or fetch health records.

2. **Hospital Management**
   - **Register Hospitals**: Add new hospitals with geolocation data.
   - **Get Nearest Hospitals**: Retrieve hospitals nearest to the user's location.
   - **View Hospitals**: List all registered hospitals.

3. **Practitioner & Appointment Management**
   - **View Available Slots**: Fetch available slots for a practitioner.
   - **Book Appointment**: Schedule an appointment with a practitioner.
   - **Reschedule Appointment**: Modify the date and time of an existing appointment.
   - **Cancel Appointment**: Cancel a previously booked appointment.

4. **FHIR Resource Management**
   - Add, fetch, and filter resources such as `Patient`, `Practitioner`, `Condition`, and `Encounter`.

---

## Installation and Setup

### Prerequisites
- Python 3.8+
- Firebase Admin SDK Key
- Postman (optional for API testing)

### Environment Variables
- `FIREBASE_KEY`: Path to the Firebase Admin SDK key.
- `APP_KEY`: Secret key for JWT authentication.

### Steps
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-directory>

2. Install dependencies:
   - pip install -r requirements.txt

3. Set environment variables:
   export FIREBASE_KEY=<path-to-firebase-key>
   export APP_KEY=<your-app-secret-key>

4. Start the server:
   python app.py
