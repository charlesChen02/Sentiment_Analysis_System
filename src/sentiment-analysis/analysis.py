from time import sleep

from couchdb import Server, PreconditionFailed
from textblob import TextBlob
import couchdb.design
import json
import os
import requests
import couchdb
from mapReduce import *

WRITE_PATH = "../../etc/formattedTweet.json"
READ_PATH = "../../assignment2-docker/tweet-harvestor-docker/tweets.json"

DUP_VIEW_ADDR = 'http://admin:couchdb@localhost:5984/parsed-tweets/_design/mapReduce/_view/dup_count'
DUP_ACT_GETIDSTR = DUP_VIEW_ADDR + '?keys=%5B\"'

suffix = '\"%5D&reduce=true&group=true'

DUP_ACT_GETID = DUP_VIEW_ADDR + '?reduce=true&group_level=2'
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
DB_NAME = "parsed-tweets"
URL = 'http://admin:couchdb@localhost:5984/'
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
        if feature == 'created_at':
            date_arr = tweet[feature].split()
            ftweet['date'] = date_arr[1] + ' ' + date_arr[2]
        if feature == "place":
            tmp = tweet[feature]
            ftweet["location"] = tmp["full_name"]
            locs = ftweet['location'].split(',')
            # print(locs)
            if len(locs) == 2:
                ftweet['state'] = ftweet['location'].split(',')[1]
                ftweet['city'] = ftweet['location'].split(',')[0]
            else:
                ftweet['state'] = ftweet['location']
                ftweet['city'] = ftweet['location']

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

    # keywords evaluation
    ftweet['tags'] = []
    words = ftweet['text'].split()
    for w in words:
        if w in AZ_KEYS:
            ftweet['tags'].append('AZ')
        if w in PZ_KEYS:
            ftweet['tags'].append('PZ')

    # Sentiment analysis
    blob = TextBlob(ftweet["text"])
    ftweet["polarity"] = blob.sentiment.polarity
    ftweet["subjectivity"] = blob.sentiment.subjectivity

    # Alternative: Add parsed tweet to local disk
    # with open(WRITE_PATH, 'w') as f:
    #     f.write(ftweet + '\n')

    return ftweet


# Clear previous output
def clearoutput():
    if os.path.isfile(WRITE_PATH):
        os.remove(WRITE_PATH)


def run():
    clearoutput()
    # we can simply add extra views inside this array,
    couch_views = [
        CountTotal(),
        CitySentiments(),
        OverallSentiments(),
        PositiveSentimentPerCity(),
        NegativeSentimentPerCity(),
        NeutralSentimentPerCity(),
        SentiByCityAndDate(),
        StrongPositiveSentimentPerCity(),
        StrongNegativeSentimentPerCity(),
        # Put other view classes here
    ]

    server = Server(url=URL)
    print("Connected to Server")

    try:
        db = server[DB_NAME]
    except:
        db = server.create(DB_NAME)
    print("create db successful")
    couchdb.design.ViewDefinition.sync(DupCount(),db)
    # Current logic: open json from READ_PATH and save into couchdb
    with open(READ_PATH, 'r') as f:
        for index, line in enumerate(f):
            # Ignore the first line or stop once we reach the end
            tweet = json.loads(line[:-1])
            # Get just the text and coordinates
            ftweet = reformattweet(tweet)
            # Alternative: Save parsed tweets to local disk
            # with open(WRITE_PATH, 'r') as doc:
            #     db.save(doc)
            # print(ftweet)

            # duplication prevention
            dup_url = DUP_ACT_GETIDSTR + ftweet['id_str'] + suffix
            r = requests.get(url=dup_url)
            resp = dict(r.json())['rows']
            if resp == []:
                db.save(ftweet)
            # sleep(1)
    print("save successful")

    couchdb.design.ViewDefinition.sync_many(db, couch_views, remove_missing=True)
    print("Views Created")

run()
