# syntax=docker/dockerfile:1

FROM python:slim-buster

WORKDIR /flask

COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "server.py"]