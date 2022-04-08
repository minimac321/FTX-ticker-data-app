FROM python:3.9

ENV PYTHONBUFFERED 1

WORKDIR /app

COPY src /app/src/
COPY requirements.txt /app/
COPY ticker_config.json /app/

RUN echo $(ls -a)

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]

