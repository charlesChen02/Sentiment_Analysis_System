import tweepy
import json, re, os, time
from cloudant.client import CouchDB
from logger import Logger
from textblob import TextBlob

TWEETS_PATH = 'tweets.json'
GEOBOX_AUSTRALIA = [112.34,-44.04,153.98,-10.41]
KEYWORD_RE = r'( az )|(astrazeneca)|(pfizer)|(novavax)|(vaccination)|(vaccine)|(vaccinate)|(vaccinated)|( dose )|(booster)|( jab )|(inoculation)|(immunisation)|(immunization)'
logger = Logger("tweet_harvestor")
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]

# Subclass StreamListener
class CouchStreamListener(tweepy.StreamListener):
    def __init__(self, db):
        super().__init__()
        self.db = db

    # def on_status(self, status):
    #     if re.search(KEYWORD_RE, status.text) is not None:
    #         logger.log("New tweet: {}".format(status.text))

    def on_data(self, data):
        if data[0].isdigit():
            pass
        else:
            json_data = json.loads(data)
            if re.search(KEYWORD_RE, json_data["text"].lower()) is not None:
                logger.log("New tweet: {}".format(json_data["text"]))
                with open(TWEETS_PATH, 'a') as tweets_file:
                    tweets_file.write(data)
                self.db.create_document(json_data)

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

# Initialize tweepy stream
def tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    couchStreamListener = CouchStreamListener(db)
    stream = tweepy.Stream(auth=api.auth, listener=couchStreamListener)
    logger.log("Tweepy stream is initialized.")
    stream.filter(locations=GEOBOX_AUSTRALIA)

# Connect CouchDB server
def couchdb_initializer(couchdb_username, couchdb_password, couchdb_address):
    try:
        client = CouchDB(couchdb_username, couchdb_password, url=couchdb_address, connect=True)
        db = client["tweets"]
        return db
    except KeyError:
        client.create_database("tweets")
        with open(TWEETS_PATH) as initial_tweets:
            for tweet in initial_tweets:
                tweet = reformattweet(tweet)
                client["tweets"].create_document(json.loads(tweet))
        db = client["tweets"]
        return db
    except:
        logger.log_error("Cannot find CouchDB Server...")
        raise

# Entry point
def run(consumer_key, consumer_secret, access_token, access_token_secret, couchdb_username, couchdb_password, couchdb_address):
    db = couchdb_initializer(couchdb_username, couchdb_password, couchdb_address)
    logger.log("Connected to CouchDB server.")
    tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db)

if __name__ == '__main__':
    time.sleep(60)
    run(os.environ['API_KEY'], os.environ['API_SECRET_KEY'], os.environ['ACESS_TOKEN'], os.environ['ACESS_TOKEN_SECRET'], os.environ['SERVER_USERNAME'], os.environ['SERVER_PASSWORD'], os.environ['SERVER_ADDRESS'])