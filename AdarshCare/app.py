import os
import pickle
import re
from logging import debug

import MySQLdb.cursors
import numpy as np
import pandas as pd
import tensorflow as tf
from chat import get_response
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_mysqldb import MySQL
# Importing libraries for Keras:
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'xyzsdfg'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'adarsh care'
  
mysql = MySQL(app)

# Loading our diabetes model:
modelDBb = pickle.load(open("models/DiabetesmodelPP.pkl", "rb"))

# Setting routes for our web-pages:
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            mesage = 'Logged in successfully !'
            return render_template('home.html', mesage = mesage)
        else:
            mesage = 'Please enter correct email / password !'
    return render_template('login.html', mesage = mesage)
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        
        # Validating email format
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address! Must be a valid Gmail address.'
        # Checking if the email already exists in the database
        elif check_email_exists(email):
            message = 'Account already exists!'
        # Validating password format
        elif not re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}$', password):
            message = 'Invalid password! Must contain at least one uppercase letter, one lowercase letter, and be at least 6 characters long.'
        # Checking if any required field is empty
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password))
            mysql.connection.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

def check_email_exists(email):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
    account = cursor.fetchone()
    return account is not None
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/diabetes")
def diabetes_prediction():
    return render_template("diabetes.html")


@app.route("/breast")
def breast():
    return render_template("breast.html")

@app.route('/food')
def foood():
    return render_template('food.html')


@app.route("/profile")
def profile():
    return render_template("profile.html")



@app.post("/predict")
def predict():
    text =request.get_json().get("message")
    
    response = get_response(text)
    message ={"answer": response}
    return jsonify(message)


@app.route("/diabetes-predict", methods=["GET", "POST"])
def db_prediction():
    if request.method == "POST":
        gender = request.form["gender"]
        age = int(request.form["age"])
        hypertension = int(request.form["hypertension"])
        heart_disease = int(request.form["heart_disease"])
        smoking_history = int(request.form["smoking_history"])
        bmi = float(request.form["bmi"])
        hba1c_level = float(request.form["hba1c_level"])
        blood_glucose_level = int(request.form["blood_glucose_level"])

        predictions = modelDBb.predict([[gender, age, hypertension, heart_disease, smoking_history, bmi, hba1c_level, blood_glucose_level,]])
        output = predictions[0]

        if output == 1 or blood_glucose_level > 110 or hba1c_level > 6:
            result = "You have Diabetes"
            emoji = "😞"
            color = "green"
        else:
            result = "You dont have Diabetes"
            emoji = "😊"
            color = "red"

        username = session.get('name')
        if username:
            message = f" {username}, {result}"
            return render_template('diabetes-result.html', message=message, emoji=emoji, color=color)

    return render_template('diabetes-result.html', message="Prediction failed", emoji="", color="")


@app.route('/breast-predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        
        basePath = os.path.dirname(__file__)
        file_path = os.path.join(basePath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        
        # Load the breast cancer model
        modelBC = load_model("breastmodel.h5")
        
        # Preprocess the image
        img = image.load_img(file_path, target_size=(256, 256))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Make the prediction
        prediction = modelBC.predict(x)
        result = prediction[0][0]
        
        if result == 1:
            output = "Malignant"
            emoji = "😞"
            color = "green"
        else:
            output = "Benign"
            emoji = "😊"
            color = "red"
            
        username = session.get('name')
        if username:
            message = f" {username}, {output}"
            return render_template('breast-result.html', message=message, emoji=emoji, color=color)

    return render_template('breast-result.html', message="Prediction failed", emoji="", color="")


if __name__ == '__main__':
    app.run(debug=True)
