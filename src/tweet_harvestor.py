import tweepy, couchdb
import json
from logger import Logger

KEYS_PATH = "etc/keys_tokens.json"
COUCH_CREDS_PATH = "etc/couch_creds.json"
GEOBOX_AUSTRALIA = [112.34,-44.04,153.98,-10.41]
FILTER_TERMS = ["Astrazanica"]
logger = Logger("tweet_harvestor")


# Initialize tweepy api
def tweepy_api_initializer():
    with open(KEYS_PATH) as json_file:
        json_object = json.load(json_file)
        consumer_key = json_object["API Key"]
        consumer_secret = json_object["API Secret Key"]
        access_token = json_object["Access Token"]
        access_token_secret = json_object["Access Token Secret"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


# Subclass StreamListener
class CouchStreamListener(tweepy.StreamListener):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def on_status(self, status):
        logger.log("New tweet: {}".format(status.text))

    def on_data(self, data):
        if data[0].isdigit():
            pass
        else:
            json_data = json.loads(data)
            self.db.save(json_data)

# Initialize tweepy stream
def tweepy_stream_initializer(api, db):
    myStreamListener = CouchStreamListener(db)
    stream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    logger.log("Twitter stream is initialized.")
    stream.filter(track=FILTER_TERMS, locations=GEOBOX_AUSTRALIA)

# Read CouchDB server
def couchdb_initializer():
    with open(COUCH_CREDS_PATH) as json_file:
        json_object = json.load(json_file)
        server = json_object["server"]
        username = json_object["username"]
        password = json_object["password"]
        database = json_object["database"]
    try:
        server = Server('https://{username}:{password}@{server}/'.format(server, username, password))
        return server[database]
    except:
        logger.log_error("Cannot find CouchDB Server...")
        raise

# Entry point
def run():
    db = couchdb_initializer()
    logger.log("Connected to CouchDB server.")
    api = tweepy_api_initializer()
    tweepy_stream_initializer(api, db)


if __name__ == '__main__':
    run()