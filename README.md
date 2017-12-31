# Bitfolio

Simple-to-use personal cryptocurrency portfolio built using Flask. Maintains a SQL database for users and transactions, provides typeahead search functionalities for all current cryptocurrencies, organizes all recorded transactions on the dashboard, and provides tools to better organize your portfolio.

<img src="img/bitfolio_home.png" width="500">
<img src="img/bitfolio_dashboard.png" width="500">
<img src="img/bitfolio_transaction.png" width="500">

### Prerequisites

```
virtualenv -p python3 /.
source bin/activate
git clone https://github.com/kevintaehyungkim/bitfolio
cd bitfolio
pip install -r requirements.txt
python bitfolio.py
```

## Current RoadMap

* Import existing coin portfolios via public key
* Line graphs for price movement; pie chart for coin distribution analysis
* Live price movements
* Ability to restructure portfolio coin order

## Author

* Kevin Kim, UC Berkeley EECS 2018

## Acknowledgments

* CryptoCompare API