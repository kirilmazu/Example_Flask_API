FROM python:3.8-slim-buster as prod

RUN mkdir /app
WORKDIR /app
RUN mkdir files

RUN pip install --upgrade pip 

COPY ./files/ /app/files/
COPY ./src/ /app/
RUN pip install -r requirements.txt

ENV DB_PATH=/app/files/example_db.db

ENV FLASK_APP=example_API.py
CMD flask run -h 0.0.0 -p 5005