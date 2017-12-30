# Author: Kevin Kim 
# Date: December 2017
# Base-URL: http://localhost:5000/

import os
import base64
import requests
from blockchain import receive_data_single, image_url
import urllib.parse
from flask import Flask
from flask import Markup
from flask import Flask, flash, redirect, url_for, request, render_template, json, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash
from Crypto import Random
from Crypto.Cipher import AES

from sqlalchemy.sql import func
# import datetime
from sqlalchemy import Column, Integer, DateTime
# created_date = Column(DateTime, default=datetime.datetime.utcnow)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bitfolio.db'
db = SQLAlchemy(app)

# Current URL
CURRENT_URL = ""

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
    __tablename__ = 'users'
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


# Transaction Class
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction = db.Column(db.String(4))
    coin = db.Column(db.String(20))
    amount = db.Column(db.Float(precision=4))
    total = db.Column(db.Float(precision=4))
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, transaction, coin, amount, total, time_created):
        self.transaction = transaction
        self.coin = coin
        self.amount = amount
        self.total = coin_price(coin, amount)
        self.time_created = time_created

    def coin_price(self, coin, amount):
        coin_price = receive_coin_data([coin])
        return coin_price * amount  


# Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    session["logged_in"] = False
    return render_template('home.html')


# User Dashboard
@app.route('/dashboard/<encrypt>')
def dashboard(encrypt=None):
    session["logged_in"] = True
    print ("DASHBOARD")
    global CURRENT_URL
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        CURRENT_URL = encrypt
        decoded_bytes = str(urllib.parse.unquote(encrypt)).encode()
        cipher = AESCipher('mysecretpassword')
        user_email = cipher.decrypt(decoded_bytes).decode("utf-8")
        user_data = User.query.filter_by(email=user_email).first()
        full_name = user_data.firstname + " " + user_data.lastname
        return render_template('dashboard.html', name=full_name)


# Transaction
@app.route('/begin_transaction', methods=['GET', 'POST'])
def begin_transaction():
    session["transaction"] = True
    print("Starting Transaction")
    if request.method == 'POST':
        coin_fullname = request.form['coin']
        coin_symbol = coin_fullname.split("(",1)[1][:-1]
        coin_name = coin_fullname.split("(",1)[0]
        coin_data = receive_data_single(coin_symbol)
        coin_price= coin_data["USD"]
        coin_url = image_url(coin_symbol)
        return render_template('transaction.html', coin=coin_name, image_url=coin_url, coin_price=coin_price)


# Transaction
@app.route('/complete_transaction', methods=['GET', 'POST'])
def complete_transaction():
    session["transaction"] = True
    print("Completing Transaction")
    if request.method == 'POST':
        print(request.form)
        transaction_type = request.form.get('type')
        trade_pair = request.form.get('pair')
        trade_price = request.form['price']
        trade_amount = request.form['amount']
        try:

            new_transaction = Transaction(transaction=transaction_type, coin=, amount=request.form['email'], total=request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            message = Markup("Invalid parameters: Please enter floats.")
            flash(message)
            return render_template('transaction.html')
        return redirect(url_for('login'))



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
    global CURRENT_URL
    session["logged_in"] = False

    if request.method == 'GET':
        if session["transaction"]:
            session["logged_in"] = True
            session["transaction"] = False
            return redirect(url_for('dashboard', encrypt=CURRENT_URL))
        else:
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
                    CURRENT_URL = url
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
    global CURRENT_URL
    session["logged_in"] = False
    CURRENT_URL = ""
    return redirect(url_for('home'))


# with coin/quantities, calculate graph based on 
def calculate_total(coin_dict):
    return


def update_total():
    return


if __name__ == "__main__":
    print ("Bitfolio Started!")
    db.create_all()
    app.secret_key = '123'
    app.debug = True
    app.run(threaded=True)
