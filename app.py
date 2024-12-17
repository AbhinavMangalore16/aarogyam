from flask import Flask, render_template
from firebase import firebase


app = Flask(__name__)
firebase = firebase.FirebaseApplication('https://aarogyam-d06ff-default-rtdb.firebaseio.com/', None)

@app.route("/")
def hello():
  return "Hello World!"

if __name__ == "__main__":
  app.run()
