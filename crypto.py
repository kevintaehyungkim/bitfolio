#/usr/bin/env python2.7

import requests
import json

from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

# pings api and receives data for multiple coins at a time.
def receive_data():
    url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=BTC,ETH&tsyms=USD"
    response = requests.get(url)
    data = response.content
    print (data)

# with coin/quantities, calculate graph based on 
def calculate_total(coin_dict):
    return num

def update_total():
    return

if __name__ == "__main__":
    receive_data()