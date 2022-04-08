FROM python:3.9

ENV PYTHONBUFFERED 1

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

RUN echo $(ls -a)

EXPOSE 80

RUN ["python", "app.py"]
