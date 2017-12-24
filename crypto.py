#/usr/bin/env python2.7
# http://localhost:5000/
import requests
import json

from flask import Flask, redirect, url_for, request, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user/<user>')
def hello(user):
    return render_template('dashboard.html', name=user)

@app.route('/login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':
      user = request.form['nm']
      return redirect(url_for('success',name = user))
   else:
      user = request.args.get('nm')
      return redirect(url_for('success',name = user))


# pings api and receives data for multiple coins at a time.
def receive_data():
    url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH&tsyms=USD"
    response = requests.get(url)
    data = response.content
    print (data)

# with coin/quantities, calculate graph based on 
def calculate_total(coin_dict):
    return

def update_total():
    return

if __name__ == "__main__":
    app.run(debug=True)
    print ("app running")