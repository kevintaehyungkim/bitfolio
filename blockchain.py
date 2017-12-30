import json
import requests

# https://www.cryptocompare.com/api

# Pings API and receives data for one coin at a time.
def receive_data_single(coin):
	url = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms=USD".format(coin)
	response = requests.get(url)
	data = response.json()
	return data

# Pings API and receives data for multiple coins at a time.
def receive_data_multiple(coin_arr):
	coins = ""
	for coin in coin_arr:
		coins += coin + ","
	coins = coins[:-1]
	url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms=USD".format(coins)
	response = requests.get(url)
	data = response.json()
	return data

# Returns PNG image url for a single coin
def image_url(coin):
	base_url = "https://www.cryptocompare.com"
	list_url = "https://www.cryptocompare.com/api/data/coinlist/"
	response = requests.get(list_url)
	coins_json = response.json()
	coins_data = coins_json["Data"]
	image_url = coins_data[coin]["ImageUrl"]
	return base_url + image_url


# Returns bitcoin balance via public key
def btc_public_key(addr):
	url = "https://blockchain.info/balance?active={}".format(addr)
	response = requests.get(url)
	data = response.json()
	# print (data["final_balance"])
	balance = data["final_balance"]
	return balance


# Updates json file with all recorded cryptocurrencies
def generate_json():
	coins = []
	url = "https://www.cryptocompare.com/api/data/coinlist/"
	response = requests.get(url)
	coins_json = response.json()
	coins_data = coins_json["Data"]
	for coin in coins_data.keys():
		coin_data = coins_data[coin]
		coins.append(coin_data["FullName"])

	with open('coin_data.json', 'w') as f:
		json.dump(coins, f, ensure_ascii=False)


if __name__ == "__main__":
	# generate_json()
	# receive_coin_data(["BTC", "ETH", "EOS", "OMG", "TRX"])
	print(image_url("BTC"))
	# btc_public_key("1AJbsFZ64EpEfS5UAjAfcUG8pH8Jn3rn1F")
