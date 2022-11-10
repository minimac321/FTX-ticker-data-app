# FTX-ticker-data-app
Create an application which fetches ticket data, stores it in a database and create endpoints to 
read this data live

The data is being streamed using [FTX](https://docs.ftx.com/#websocket-api) websockets. To use this application, you will need to create an account and get API credentials


##  Installation

```
# Clone this repository
git clone git@github.com:minimac321/centauri-ticker-data-app.git

# Enter the repository dir
cd centauri-ticker-data-app

# Create a python virtual environment and activate it
virtualenv -p /usr/bin/python3.9 ticker_app_env

# Install all required dependencies
pip install -r requirements.txt
```


Create a `.env` file in the project root directory to hold your FTX API credentials as below:
```
FTX_API_KEY=XYZ
FTX_API_SECRET=123
```

Build the docker images
```
docker-compose build
```

Start the docker container
```
docker-compose up -d
```

Now our Database and flask application are running in a terminal

We need to run out data streaming script with 
```
python src/ticker_data_streaming.py
```
Once the script is running, we can query the database for the latest data using any browser or [postman](https://www.postman.com/) 


## Endpoint commands

- Fetch all data:
  - 127.0.0.1/symbol_spread
  

- Fetch all data for a single symbol
  - 127.0.0.1/symbol_spread/ETH/USD/


- Fetch the most recent entry for a given symbol
  - 127.0.0.1/symbol_spread/ETH/USD/ask


- Fetch ASK price for closest entry using a timestamp
  - 127.0.0.1/symbol_spread/ETH/USD/ask?timestamp=1648995959


- Fetch BID price for closest entry using a timestamp
  - 127.0.0.1/symbol_spread/ETH/USD/bid?timestamp=1648995959


## Postgres DB

To take a look under the hood at the actual postgres database use:
- docker exec -it postgres_db psql -U postgres
