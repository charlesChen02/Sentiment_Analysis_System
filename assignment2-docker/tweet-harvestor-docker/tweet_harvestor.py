import tweepy
import json, re, os
from couchdb.client import Server
from logger import Logger

TWEETS_PATH = 'tweets.json'
GEOBOX_AUSTRALIA = [112.34,-44.04,153.98,-10.41]
KEYWORD_RE = r'(astrazeneca)|(pfizer)|(novavax)|(vaccination)|(vaccine)|(vaccinate)|(vaccinated)|(dose)|(booster)|(jab)|(inoculation)|(immunisation)|(immunization)'
logger = Logger("tweet_harvestor")


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
                self.db.save(json_data)


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
def couchdb_initializer(couchdb_address):
    try:
        server = Server(couchdb_address)
        print(server.stats())
        if "tweets" not in server:
            server.create("tweets")
        return server["tweets"]
    except:
        logger.log_error("Cannot find CouchDB Server...")
        raise

# Entry point
def run(consumer_key, consumer_secret, access_token, access_token_secret, couchdb_address):
    db = couchdb_initializer(couchdb_address)
    logger.log("Connected to CouchDB server.")
    tweepy_stream_initializer(consumer_key, consumer_secret, access_token, access_token_secret, db)

if __name__ == '__main__':
    run(os.environ['API_KEY'], os.environ['API_SECRET_KEY'], os.environ['ACESS_TOKEN'], os.environ['ACESS_TOKEN_SECRET'], os.environ['SERVER_ADDRESS'])