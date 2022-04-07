FROM python:3.9




FROM python:3.9

ENV PYTHONBUFFERED 1

COPY requirements.txt .

RUN pip install --upgrade pip

# Do we need it ??
# RUN apt-get update \
#   && apt-get upgrade -y \
#   && apt-get install -y libpq-dev gcc musl-dev libffi-dev \
#   && apt-get clean

RUN pip install -r requirements.txt

COPY . .

RUN echo $(ls)

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]