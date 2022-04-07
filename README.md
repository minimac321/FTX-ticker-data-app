# centauri-ticker-data-app
Create an application which fetches ticket data, stores it in a database and create endpoints to fetch this data from



## Setup Guide

Build the docker images
```
docker-compose build
```

Start the docker container
```
docker-compose up
```


Now our Database and flask application are running in a terminal

We need to run out data streaming script with 
```
python ticker_data_streaming.py
```
Once the script is running, we can query the database for the latest data using any browser or [postman](https://www.postman.com/) 


# Endpoint commands

- Fetch all data:
  - 127.0.0.1/symbol_spread


- Fetch all data for a single symbol
  - 127.0.0.1/symbol_spread/ETH/USD/


- Fetch ASK price for closest entry using a timestamp
  - 127.0.0.1/ETH/USD/ask?timestamp=1648995959


- Fetch BID price for closest entry using a timestamp
  - 127.0.0.1/ETH/USD/bid?timestamp=1648995959





### TODO

##### Code
- Try get the main dockerfile to trigger the ticker_data_streaming.py or ingest that into the 
app.py class
- Doc Strings
- Config type files
- Check for available Symbols
- Persistent data (volume attached?)



- Doc Write up
  - Why docker
  - Why postgres and flask (pros vs cons)
  - Why on a single table

Improvements:
- Code structure: Docker mainly to allow progress
- FastAPI ?
- More concurrency

Issues / Limitations:
- Docker



<br>


What to dicuss:
- How this changes from local to Cloud
- Why I used postgres and Flask
- 



Link: [https://phoenixnap.com/kb/mysql-docker-container]
- Look here if I need to configure the mysql container

How to access the mysql data base through linux commands:
- Run the mysql docker image
  - sudo docker run --name=mysql-container -d mysql/mysql-server:latest
  - Check that it's running with `docker ps` 
- Connect to the MySQL Docker Container
  - call: `apt-get install mysql-client`
  - Generated password: "0zTfi7o#6.8.yZ7d5Aj^2M=&QEB7:u%j"
  - Changed password to "root"


Commands:
* docker exec -it ticker_db psql -U postgres
* Steps to re-init docker:
  * docker-compose build --no-cache
  * docker-compose up --force-recreate
* docker-compose down: Shuts down all docker images
* docker volume rm centauri-ticker-data-app_pgdata: to clear the volume which is like the data 
store

SQL Statements:
- select * from bid_ask;
- INSERT INTO bid_ask (bid,ask,bid_size,ask_size,last,time,symbol,datetime) VALUES (116.63,116.67,66.06,69.84,116.695,1649355188.3697891,'SOL/USD','2022/04/07 18:13:08');



## Questions:
- Websocket vs RestAPI on FTX in terms of speed decay