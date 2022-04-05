FROM python:3.9.5

# The environment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONBUFFERED 1
#
# RUN apt-get update \
#   && apt-get upgrade -y \
#   && apt-get install -y libpq-dev gcc musl-dev libffi-dev \
#   && apt-get clean

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN echo $(ls)

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]