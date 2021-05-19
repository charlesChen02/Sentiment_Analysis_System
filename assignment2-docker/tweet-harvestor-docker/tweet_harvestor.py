import couchdb
import tweepy
import json, re, os, time
from cloudant.client import CouchDB
from logger import Logger
from textblob import TextBlob
from mapReduce import *
import requests

TWEETS_PATH = 'tweets.json'
GEOBOX_AUSTRALIA = [112.34,-44.04,153.98,-10.41]
KEYWORD_RE = r'( az )|(astrazeneca)|(pfizer)|(novavax)|(vaccination)|(vaccine)|(vaccinate)|(vaccinated)|( dose )|(booster)|( jab )|(inoculation)|(immunisation)|(immunization)'
logger = Logger("tweet_harvestor")
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
AZ_KEYS = set()
PZ_KEYS = set()
DB_NAME = "parsed-tweets"
suffix = '\"%5D&reduce=true&group=true'
DUP_VIEW_ADDR = 'http://admin:couchdb@localhost:5984/parsed-tweets/_design/mapReduce/_view/dup_count'
DUP_ACT_GETIDSTR = DUP_VIEW_ADDR + '?keys=%5B\"'




# Subclass StreamListener
class CouchStreamListener(tweepy.StreamListener):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def on_data(self, data):
        if data[0].isdigit():
            pass
        else:
            json_data = json.loads(data)
            if re.search(KEYWORD_RE, json_data["text"].lower()) is not None:
                logger.log("New tweet: {}".format(json_data["text"]))
                with open(TWEETS_PATH, 'a') as tweets_file:
                    tweets_file.write(data)
                ftweet = reformattweet(json_data)
                dup_url = DUP_ACT_GETIDSTR + ftweet['id_str'] + suffix
                r = requests.get(url=dup_url)
                resp = dict(r.json())['rows']
                if resp == []:
                    self.db.create_document(ftweet)


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

# Initialize tweepy stream
def tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    couchStreamListener = CouchStreamListener(db)
    stream = tweepy.Stream(auth=api.auth, listener=couchStreamListener)
    logger.log("Tweepy stream is initialized.")
    while(True):
        try:
            stream.filter(locations=GEOBOX_AUSTRALIA)
        except:
            pass

# Connect CouchDB server
def couchdb_initializer(couchdb_username, couchdb_password, couchdb_address):
    try:
        client = CouchDB(couchdb_username, couchdb_password, url=couchdb_address, connect=True)

        db = client[DB_NAME]
        return db
    except KeyError:
        client.create_database(DB_NAME)
        with open(TWEETS_PATH) as initial_tweets:
            for tweet in initial_tweets:
                tweet = reformattweet(tweet)
                client[DB_NAME].create_document(json.loads(tweet))
        db = client[DB_NAME]
        return db
    except:
        logger.log_error("Cannot find CouchDB Server...")
        raise

# Entry point
def run(consumer_key, consumer_secret, access_token, access_token_secret, couchdb_username, couchdb_password, couchdb_address):
    db = couchdb_initializer(couchdb_username, couchdb_password, couchdb_address)
    couchdb.design.ViewDefinition.sync(DupCount(), db)
    logger.log("Connected to CouchDB server.")

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
        OverallStateSentiments(),
        # Put other view classes here
    ]
    couchdb.design.ViewDefinition.sync_many(db, couch_views, remove_missing=True)

    tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db)

if __name__ == '__main__':
    run(os.environ['API_KEY'], os.environ['API_SECRET_KEY'], os.environ['ACESS_TOKEN'], os.environ['ACESS_TOKEN_SECRET'], os.environ['SERVER_USERNAME'], os.environ['SERVER_PASSWORD'], os.environ['SERVER_ADDRESS'])