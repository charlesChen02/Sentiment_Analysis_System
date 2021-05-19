# syntax=docker/dockerfile:1

FROM python:slim-buster

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "tweet_harvestor.py"]