# Author: Kevin Kim 
# Date: December 2017
# Base-URL: http://localhost:5000/

import os
import base64
import datetime
import requests
import operator
import urllib.parse
from blockchain import receive_data_single, receive_data_multiple, generate_data
from flask import Flask
from flask import Markup
from flask import Flask, flash, redirect, url_for, request, render_template, json, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash
from Crypto import Random
from Crypto.Cipher import AES
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, DateTime, desc
# from sqlalchemy import desc
# created_date = Column(DateTime, default=datetime.datetime.utcnow)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bitfolio.db'
db = SQLAlchemy(app)

# Current
CURRENT_URL = ""
CURRENT_EMAIL = ""

#CryptoCompare Base URL
CRYPTO_BASE_URL = "https://www.cryptocompare.com"

#Read JSON data into the coin_database variable
with open('coin_data.json', 'r') as f:
    coin_database = json.load(f)

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
    email = db.Column(db.String(45))
    transaction = db.Column(db.String(4))
    coin = db.Column(db.String(20))
    amount = db.Column(db.Float(precision=4))
    total = db.Column(db.Float(precision=4))
    time_created = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, email, transaction, coin, amount):
        self.email = email
        self.transaction = str(transaction)
        self.coin = str(coin)
        self.amount = float(amount)
        self.total = self.coin_price(coin, amount)
        self.time_created = datetime.datetime.now()

    def coin_price(self, coin, amount):
        coin_price = (receive_data_single(coin))["USD"]
        return float(float(coin_price) * amount)


# Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    session["logged_in"] = False
    session["transaction"] = False
    return render_template('home.html')


# User Dashboard
@app.route('/dashboard/<encrypt>')
def dashboard(encrypt=None):
    print ("Loading Dashboard")
    session["logged_in"] = True
    global CURRENT_URL
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        acc_total = 0.0
        transactions = []
        coin_holdings = {}
        coin_portfolio = []
        CURRENT_URL = encrypt
        decoded_bytes = str(urllib.parse.unquote(encrypt)).encode()
        cipher = AESCipher('mysecretpassword')
        user_email = cipher.decrypt(decoded_bytes).decode("utf-8")
        user_data = User.query.filter_by(email=user_email).first()
        full_name = user_data.firstname + " " + user_data.lastname

        data = Transaction.query.filter_by(email=user_email).all()
        for d in data:
            acc_total += d.total
            if d.coin in coin_holdings:
                coin_holdings[d.coin] += d.amount
            else:
                coin_holdings[d.coin] = d.amount

        # sorted(coin_holdings.items(), key=lambda x: x[1], reverse=True)

        coin_list = list(coin_holdings.keys())
        if len(coin_list) > 0:
            coin_prices = receive_data_multiple(coin_list)['RAW']

            for c in coin_holdings.keys():
                coin = dict(name=c, curr_price=("%.2f" % coin_prices[c]['USD']['PRICE']), holdings=("%.2f" % coin_holdings[c]), image_url=CRYPTO_BASE_URL+coin_database[c]["ImageUrl"],total=("%.2f" % float(coin_prices[c]['USD']['PRICE']*coin_holdings[c])), change=("%.2f" % float(coin_prices[c]['USD']['CHANGEPCT24HOUR'])))
                coin_portfolio.append(coin)

            sorted(coin_portfolio, key=lambda k: k['total'])

            entities = Transaction.query.filter(Transaction.email == user_email).order_by(desc(Transaction.time_created)).limit(5).all()
            if entities:
                for entity in entities:
                    if entity.transaction == 'BUY':
                        transaction = dict(type=entity.transaction, coin=entity.coin, image_url=CRYPTO_BASE_URL+coin_database[entity.coin]["ImageUrl"], quantity=entity.amount, value=("%.2f" % entity.total), date=entity.time_created.strftime('%m/%d/%Y %H:%M'))
                    elif entity.transaction == 'SELL':
                        transaction = dict(type=entity.transaction, coin=entity.coin, image_url=CRYPTO_BASE_URL+coin_database[entity.coin]["ImageUrl"], quantity=entity.amount, value=-1.0*float("%.2f" % entity.total), date=entity.time_created.strftime('%m/%d/%Y %H:%M'))
                    transactions.append(transaction)

            if len(transactions) < 5:
                for i in range(0, 5-len(transactions)):
                    transaction = dict(type=" ", coin=" ", quantity=" ", value=" ", date=" ")

    return render_template('dashboard.html', name=full_name, total_bal=float("%.2f" % acc_total), transactions=transactions, coin_portfolio=coin_portfolio)


# Transaction
@app.route('/begin_transaction', methods=['GET', 'POST'])
def begin_transaction():
    session["transaction"] = True
    print("Starting Transaction")
    if request.method == 'POST':
        coin_fullname = request.form['coin']
        coin_symbol = coin_fullname.split("(",1)[1][:-1]
        coin_data = receive_data_single(coin_symbol)
        coin_price = coin_data["USD"]
        return render_template('transaction.html', coin=coin_database[coin_symbol]["CoinName"], image_url=CRYPTO_BASE_URL+coin_database[coin_symbol]["ImageUrl"], coin_price=coin_price, coin_symbol=coin_symbol)


# Transaction
@app.route('/complete_transaction', methods=['GET', 'POST'])
def complete_transaction():
    session["transaction"] = True
    print("Completing Transaction")
    if request.method == 'POST':
        transaction_type = request.form.get('type')
        trade_pair = request.form.get('pair')
        trade_price = request.form['price']
        trade_amount = request.form['amount']
        coin_symbol = trade_pair.split("/", 1)[0]
        coin_data = receive_data_single(coin_symbol)
        coin_price= coin_data["USD"]

        try:
            if transaction_type == 'BUY':
                new_transaction = Transaction(email=CURRENT_EMAIL, transaction=transaction_type, coin=coin_symbol, amount=float(trade_amount))
            elif transaction_type == 'SELL':
                data = Transaction.query.filter_by(coin=coin_symbol).all()
                coin_total = 0.0
                for d in data:
                    coin_total += d.amount
                if coin_total > 0 and float(trade_amount) <= coin_total:
                    new_transaction = Transaction(email=CURRENT_EMAIL, transaction=transaction_type, coin=coin_symbol, amount=-1.0*float(trade_amount))
                else:
                    message = Markup("You don't have enough coins.")
                    flash(message)
                    return render_template('transaction.html', coin=coin_database[coin_symbol]["CoinName"], image_url=CRYPTO_BASE_URL+coin_database[coin_symbol]["ImageUrl"], coin_price=coin_price, coin_symbol=coin_symbol)
        except Exception as e:
            print(e)
            message = Markup("Invalid parameters: Please enter valid price and amount.")
            flash(message)
            return render_template('transaction.html', coin=coin_database[coin_symbol]["CoinName"], image_url=CRYPTO_BASE_URL+coin_database[coin_symbol]["ImageUrl"], coin_price=coin_price, coin_symbol=coin_symbol)

        try:
            db.session.add(new_transaction)
            db.session.commit()
        except Exception as e:
            print(e)
            message = Markup("Failed to record transaction. Please try again.")
            flash(message)
            return render_template('transaction.html', coin=coin_database[coin_symbol]["CoinName"], image_url=CRYPTO_BASE_URL+coin_database[coin_symbol]["ImageUrl"], coin_price=coin_price, coin_symbol=coin_symbol)

        return redirect(url_for('login'))


# Clear all Transactions
@app.route("/clear", methods=['GET', 'POST'])
def clear():
    print ("Clearing all transactions")
    if request.method == 'POST':
        session["logged_in"] = True
        session["transaction"] = False
        try:
            num_rows_deleted = db.session.query(Transaction).delete()
            db.session.commit()
        except:
            db.session.rollback()
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
    global CURRENT_EMAIL

    if session["transaction"] or session["logged_in"]:
            session["logged_in"] = True
            session["transaction"] = False
            return redirect(url_for('dashboard', encrypt=CURRENT_URL))

    if request.method == 'GET':
        return render_template('login.html')
    else:

        if session["logged_in"]:
            return redirect(url_for('dashboard', encrypt=CURRENT_URL))

        post_email = request.form['email']
        post_password = request.form['password']
        CURRENT_EMAIL = post_email
        try:
            data = User.query.filter_by(email=post_email).first()
            if data is not None:
                if check_password_hash(data.password, post_password):
                    cipher = AESCipher('mysecretpassword')
                    encrypted_email = cipher.encrypt(CURRENT_EMAIL)
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
    return render_template('login.html')

# Logout
@app.route("/logout")
def logout():
    global CURRENT_URL
    global CURRENT_EMAIL
    session["logged_in"] = False
    CURRENT_URL = ""
    CURRENT_EMAIL = ""
    return redirect(url_for('home'))


# with coin/quantities, calculate graph based on 
def calculate_total(coin_dict):
    return


def update_total():
    return


if __name__ == "__main__":
    print ("Bitfolio Started!")
    generate_data()
    db.create_all()
    app.secret_key = '123'
    app.debug = True
    app.run(threaded=True)

