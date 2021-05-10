from textblob import TextBlob
import json
import os
import requests
import couchdb

WRITE_PATH = "../../etc/formattedTweets.json"
READ_PATH = "../../etc/example.json"
NECESSARY_CONTENTS = ["id_str", "created_at", "text", "timestamp_ms", "place"]
url = 'https://localhost:5984/exampledb'


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
    with open(READ_PATH, 'r') as f:
        for index, line in enumerate(f):
            # Ignore the first line or stop once we reach the end
            tweet = json.loads(line[:-1])
            # Get just the text and coordinates
            tweet = reformattweet(tweet)

run()
