# http://localhost:5000/

import os
import json
import base64
import requests
import urllib.parse
from flask import Flask
from flask import Markup
from flask import Flask, flash, redirect, url_for, request, render_template, json, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash
from Crypto import Random
from Crypto.Cipher import AES

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bitfolio.db'
db = SQLAlchemy(app)

# AES Padding
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[0:-s[-1]]

# AES Cipher
class AESCipher:

    def __init__( self, key ):
        self.key = key

    def encrypt( self, raw ):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) )

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))


# User Class
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(45))
    lastname = db.Column(db.String(45))
    email = db.Column(db.String(45), unique=True)
    password = db.Column(db.String)

    def __init__(self, firstname, lastname, email, password):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.hash_password(password)

    def hash_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    session["logged_in"] = False
    return render_template('home.html')


# User Dashboard
@app.route('/dashboard/<encrypt>')
def dashboard(encrypt=None):
    print ("DASHBOARD")
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        decoded_bytes = str(urllib.parse.unquote(encrypt)).encode()
        cipher = AESCipher('mysecretpassword')
        user_email = cipher.decrypt(decoded_bytes).decode("utf-8")
        user_data = User.query.filter_by(email=user_email).first()
        return render_template('dashboard.html', name=user_data.firstname)


# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        try:
            new_user = User(firstname=str.capitalize(request.form['firstname']), lastname=str.capitalize(request.form['lastname']), email=request.form['email'], password=request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            message = Markup("Account already exists!")
            flash(message)
            return render_template('signup.html')
    return render_template('signup.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    #
    session["logged_in"] = False
    if request.method == 'GET':
        return render_template('login.html')
    else:
        post_email = request.form['email']
        post_password = request.form['password']
        try:
            data = User.query.filter_by(email=post_email).first()
            if data is not None:
                if check_password_hash(data.password, post_password):
                    cipher = AESCipher('mysecretpassword')
                    encrypted_email = cipher.encrypt(post_email)
                    url = urllib.parse.quote_from_bytes(encrypted_email, safe='')
                    session["logged_in"] = True
                    return redirect(url_for('dashboard', encrypt=url))
                else:
                    message = Markup("Invalid Email or Password")
                    flash(message)
                    return render_template('login.html')
            else:
                message = Markup("Account does not exist")
                flash(message)
                return render_template('login.html')
        except:
            message = Markup("Login Failed. Please try again.")
            flash(message)
            return render_template('login.html')

# Logout
@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect(url_for('home'))


# Pings API and receives data for multiple coins at a time.
def receive_coin_data(coin):

    url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH&tsyms=USD"
    response = requests.get(url)
    data = response.json()
    return (data[coin]["USD"])
    # print (data[0])
    # print (data[1])
    # print (data)

# with coin/quantities, calculate graph based on 
def calculate_total(coin_dict):
    return

def update_total():
    return

if __name__ == "__main__":
    print ("app running")
    db.create_all()
    app.secret_key = '123'
    app.debug = True
    app.run(threaded=True)
