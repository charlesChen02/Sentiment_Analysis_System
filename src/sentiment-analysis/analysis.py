from textblob import TextBlob
import json
import os
import requests
import couchdb

WRITE_PATH = "../../etc/formattedTweets.json"
READ_PATH = "../../etc/example.json"
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
url = 'https://localhost:5984/exampledb'


class TweetStore(object):
    def __init__(self, dbname, url="http://127.0.0.1:5984/"):
        try:
            self.server = couchdb.Server(url=url)
            self.db = self.server.create(dbname)
            self._create_views()
        except couchdb.http.PreconditionFailed:
            self.db = self.server[dbname]

    def _create_views(self):
        # mapreduce for counting total number of tweets collected
        count_total = 'function(doc) {emit(doc.id,1);}'

        count_reduce = "_sum" # This seems to be the built in function for the couchdb.
        view = couchdb.design.ViewDefinition('twitter',
                                             'count_tweets',
                                             count_total,
                                             reduce_fun=count_reduce)
        view.sync(self.db)
        # view for showing all stored tweets
        get_tweets = \
            'function(doc) { emit(("0000000000000000000"+doc.id).slice(-19), doc); }'
        view = couchdb.design.ViewDefinition('twitter', 'get_tweets', get_tweets)
        view.sync(self.db)

        # mapreduce for overall sentiment level
        eval_sentiment = "function(doc) {emit(doc.id,doc.polarity);}"
        sentiment_reduce = "function(keys,values,rereduce) {"\
                           "return sum(values);" \
                           "}"
        view = couchdb.design.ViewDefinition('twitter',
                                             'sentiment_score',
                                             eval_sentiment,
                                             reduce_fun=sentiment_reduce)
        view.sync(self.db)

        # Sentiment level break down
        break_sentiment = "function(doc) {emit([doc.id,doc.place.location],doc.polarity);}"
        reduce_by_city = None # currently in tmp.js
        view = couchdb.design.ViewDefinition('twitter',
                                             'sentiment_score',
                                             break_sentiment,
                                             reduce_fun=reduce_by_city) 
        view.sync(self.db)

        #TODO: number of positive/negative posts for each city
        


    def save_tweet(self, tw):
        tw['_id'] = tw['id_str']
        self.db.save(tw)

    def count_tweet(self):
        for doc in self.db.view('twitter/count_tweets'):
            return doc.value

    def get_tweet(self):
        return self.db.view('twitter/get_tweets')

    def get_sentiment(self):
        for doc in self.db.view('twitter/sentiment_score'):
            return doc.value


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

    blob = TextBlob(ftweet["text"])
    ftweet["polarity"] = blob.sentiment.polarity
    ftweet["subjectivity"] = blob.sentiment.subjectivity
    ftweet = json.dumps(ftweet)
    with open(WRITE_PATH, 'w') as f:
        f.write(ftweet + '\n')

    # postTweet()

    return ftweet


# Clear previous output
def clearoutput():
    if os.path.isfile(WRITE_PATH):
        os.remove(WRITE_PATH)


def run():
    clearoutput()
    storage = TweetStore('test_db')
    with open(READ_PATH, 'r') as f:
        for index, line in enumerate(f):
            # Ignore the first line or stop once we reach the end
            tweet = json.loads(line[:-1])
            # Get just the text and coordinates
            tweet = reformattweet(tweet)
            storage.save_tweet(tweet)



run()
