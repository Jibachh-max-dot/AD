import os
import pickle
import re
from logging import debug

import MySQLdb.cursors
import numpy as np
import pandas as pd
import tensorflow as tf
from flask import Flask, redirect, render_template, request, session, url_for
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
modelDB = pickle.load(open("models/LogModelDiabetes.pkl", "rb"))
modelBC = pickle.load(open("models/RFModelCancer.pkl", "rb"))



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
  
@app.route('/register', methods =['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            mesage = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address !'
        elif not userName or not password or not email:
            mesage = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user (name, email, password) VALUES (%s, %s, %s)', (userName, email, password))
            mysql.connection.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template('register.html', mesage = mesage)
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/diabetes")
def diabetes_prediction():
    return render_template("diabetes.html")


@app.route("/cancer")
def cancer_prediction():
    return render_template("cancer.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/diabetes-predict", methods=["GET", "POST"])
def db_prediction():
    if request.method == "POST":

        pregnancies = int(request.form["pregnancies"])
        glucose = int(request.form["glucose"])
        bp = int(request.form["bp"])
        skin_thickness = int(request.form["skin_thickness"])
        insulin = int(request.form["insulin"])
        bmi = int(request.form["bmi"])
        dpf = int(request.form["dpf"])
        glucose = int(request.form["glucose"])

        predictions = modelDB.predict([[pregnancies, glucose, bp, skin_thickness, insulin, bmi, dpf, glucose]])
        output = predictions[0]

        if output == 0:
            result = "The patient doesn't have Diabetes"
        else:
            result = "The patient has Diabetes"

    return render_template('diabetes-result.html', prediction_text=result)

@app.route('/predict', methods = ['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        
        basePath = os.path.dirname(__file__)
        file_path = os.path.join(
            basePath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        
        # Making our prediction:
        prediction = model_predict(file_path, modelCV)
        result = prediction
        return result
    return None


if __name__ == '__main__':
    app.run(debug=True)
