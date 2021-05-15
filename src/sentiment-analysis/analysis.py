from time import sleep

from couchdb import Server
from textblob import TextBlob
import couchdb.design
import json
import os
import requests
import couchdb
from mapReduce import *

WRITE_PATH = "../../etc/formattedTweet.json"
READ_PATH = "../../assignment2-docker/tweet-harvestor-docker/tweets.json"

NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
# url = os.environ['SERVER_ADDRESS']

url = 'http://admin:couchdb@localhost:5984/'
AZ_KEYS = set()
PZ_KEYS = set()

'''
Input: 
    tweet: single tweet that just harvested from harvester
Output:
    ftweet: formatted tweet which only contain necessary info, 
            ready to be fed into DB
'''


def reformattweet(tweet):
    ftweet = {}
    for feature in NECESSARY_CONTENTS:
        if feature == "place":
            tmp = tweet[feature]
            ftweet["location"] = tmp["full_name"]
            ftweet["country"] = tmp["country"]
            ftweet["bounding_box"] = {}
            for index, coord in enumerate(tmp["bounding_box"]["coordinates"][0]):

                if index == 0:
                    ftweet["bounding_box"]["xmin"] = coord[0]
                    ftweet["bounding_box"]["ymin"] = coord[1]
                elif index == 2:
                    ftweet["bounding_box"]["xmax"] = coord[0]
                    ftweet["bounding_box"]["ymax"] = coord[1]
            continue
        ftweet[feature] = tweet[feature]
    words = ftweet['text'].split()

    blob = TextBlob(ftweet["text"])
    ftweet["polarity"] = blob.sentiment.polarity
    ftweet["subjectivity"] = blob.sentiment.subjectivity

    # ftweet = json.dumps(ftweet)

    # with open(WRITE_PATH, 'w') as f:
    #     f.write(ftweet + '\n')

    # postTweet()

    return ftweet


# Clear previous output
def clearoutput():
    if os.path.isfile(WRITE_PATH):
        os.remove(WRITE_PATH)


def run():
    clearoutput()
    # we can simply add extra views inside this array,

    # those views would only be computed when queried
    couch_views = [
        CountTotal(),
        CitySentiments(),
        OverallSentiments(),
        PositiveSentimentPerCity(),
        NegativeSentimentPerCity(),
        NeutrarlSentimentPerCity(),
        # Put other view classes here
    ]

    server = Server(url=url)
    # try:
    #     db = server["parsed-tweets"]
    # except KeyError:
    print("Connected to Server")
    try:
        db = server["parsed-tweets"]
    except:
        db = server.create("parsed-tweets")
    print("create db successful")
    # Current logic: open json from READ_PATH and save into couchdb
    # with open(READ_PATH, 'r') as f:
    #     for index, line in enumerate(f):
    #         # Ignore the first line or stop once we reach the end
    #         tweet = json.loads(line[:-1])
    #         # Get just the text and coordinates
    #         ftweet = reformattweet(tweet)
    #         # with open(WRITE_PATH, 'r') as doc:
    #         #     db.save(doc)
    #         # print(ftweet)
    #         # break
    #         print(ftweet)
    #         db.save(ftweet)
    #         print("save successful")
    #         sleep(2)
    couchdb.design.ViewDefinition.sync_many(db, couch_views, remove_missing=True)
    print("Views Created")


run()
