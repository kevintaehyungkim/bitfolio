#/usr/bin/env python2.7
# http://localhost:5000/
import json
import requests
from flask import Flask, redirect, url_for, request, render_template, json
from flask.ext.mysql import MySQL 
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'lolkevin123'
app.config['MYSQL_DATABASE_DB'] = 'bitfolio'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

# home page
@app.route('/')
def home():
    return render_template('home.html')

# dashboard
@app.route('/user/<user>')
def hello(user):
    return render_template('dashboard.html', name=user, total_val=receive_coin_data("BTC"))

# signup page
@app.route('/signup')
def show_signup():
    return render_template('signup.html')

# signup
@app.route('/createuser', methods=['POST'])
def signup():
    # user information obtained from the signup form
    firstname = request.form['inputFirstName']
    lastname = request.form['inputLastName']
    email = request.form['inputEmail']
    password = request.form['inputPassword']
    
    # validate the received values
    if firstname and lastname and email and password:
        # mysql
        hashed_password = generate_password_hash(password)
        cursor.callproc('create_user',(firstname, lastname, email, hashed_password))
        data = cursor.fetchall()

        if len(data) is 0:
            # return json.dumps({'message':'User created successfully !'})
            return redirect(url_for('login'))
        else:
            return json.dumps({'error':str(data[0])})

    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})


# login page
@app.route('/login')
def login():
    return render_template('login.html')



# login page
# @app.route('/login',methods = ['POST', 'GET'])
# def login():
#    if request.method == 'POST':
#       user = request.form['nm']
#       return redirect(url_for('success',name = user))
#    else:
#       user = request.args.get('nm')
#       return redirect(url_for('success',name = user))


# pings api and receives data for multiple coins at a time.
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
    receive_data()
    app.run(debug=True)
    print ("app running")