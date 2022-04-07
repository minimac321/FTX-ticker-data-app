# centauri-ticker-data-app
Create an application which fetches ticket data, stores it in a database and create endpoints to fetch this data from

<br>

Program flow:
- Start the main application docker image to host the endpoints, followed by the image for postgres 
DB which can house the data.
- The main application will trigger a streaming module which will spawn N threads which each open a
websocket for a symbol and write data using the POST endpoint to the postgres DB  
- To check the data available - we can use postman to check if the data is changing, and 
even query with a selected time stamp.


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
