from flask import Flask, send_from_directory, jsonify
from flask_restful import Api, Resource
import json,os
import math
import requests



# coubdb_auth_token =  os.environ['COUCHDB_AUTH_TOKEN']
# coudb_ip = os.environ['SERVER_IP']


coubdb_auth_token =  'YWRtaW46Y291Y2hkYg=='
coudb_ip = '127.0.0.1'

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + coubdb_auth_token 
}

def get_total_tweets():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/count_total?reduce=true&group=true".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_overall_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/overall_sentiments".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_positive_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/positive_sentiment_per_state".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_negative_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/negative_sentiment_per_state".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_neutral_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/neutral_sentiment_per_state".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_strong_negative_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/strong_negative_sentiment_per_state".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_strong_positive_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/strong_positive_sentiment_per_state".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_overall_sentiment_by_date():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/senti_by_city_and_date?reduce=true&group_level=1".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    return response.json()

def get_state_sentiment():
    url = "http://{}:5984/parsed-tweets/_design/mapReduce/_view/overall_state_sentiments?reduce=true&group_level=2".format(coudb_ip)
    response = requests.request("GET", url, headers=headers)
    data = response.json()['rows']
    intermediate_data = {
        'Australian Capital Territory':{'sum':0,'count':0},
        'New South Wales':{'sum':0,'count':0},
        'Victoria':{'sum':0,'count':0},
        'Western Australia':{'sum':0,'count':0},
        'Queensland':{'sum':0,'count':0},
        'South Australia':{'sum':0,'count':0},
        'Northern Territory':{'sum':0,'count':0}
    }
    print(list(intermediate_data.keys()))
    for record in data:
        clean_key = record['key'].strip()
        if clean_key in list(intermediate_data.keys()):
            intermediate_data[clean_key]['sum'] += record['value']['sum']
            intermediate_data[clean_key]['count'] += record['value']['count']
        elif clean_key not in list(intermediate_data.keys()):
            if clean_key.lower() == "brisbane":
                intermediate_data['Queensland']['sum'] += record['value']['sum']
                intermediate_data['Queensland']['count'] += record['value']['count']
            elif clean_key.lower() == "canberra":
                intermediate_data['Australian Capital Territory']['sum'] += record['value']['sum']
                intermediate_data['Australian Capital Territory']['count'] += record['value']['count']
            elif clean_key.lower() == "melbourne":
                intermediate_data['Victoria']['sum'] += record['value']['sum']
                intermediate_data['Victoria']['count'] += record['value']['count']
            elif clean_key.lower() == "perth (wa)":
                intermediate_data['Western Australia']['sum'] += record['value']['sum']
                intermediate_data['Western Australia']['count'] += record['value']['count']
            elif clean_key.lower() == "sydney":
                intermediate_data['New South Wales']['sum'] += record['value']['sum']
                intermediate_data['New South Wales']['count'] += record['value']['count']

    return {key:(math.ceil(rescaling(-1,1,0,100,value['sum']/value['count'])) if value['count']!=0 else 50) for key, value in intermediate_data.items()}

server = Flask(__name__, static_url_path='', static_folder='../Client/build')
api = Api(server)

# helper functions

def rescaling(old_min, old_max, new_min,new_max,value):
    return (new_max-new_min)*(value-old_max)/(old_max-old_min) + new_max

@server.route("/", defaults={'path': ''})
def index(path):
    return send_from_directory(server.static_folder, 'index.html')


@server.route("/api/insightsOverview", methods=['GET'])
def insightsOverview():
    total_tweets = get_total_tweets()['rows'][0]["value"]
    overall_sentiment  = get_overall_sentiment()['rows'][0]["value"]["sum"]/total_tweets
    rescaled_overall_sentiment = rescaling(-1,1,0,100,overall_sentiment)/100
    postive_sentiment_tweets = get_positive_sentiment()['rows'][0]["value"]
    negative_sentiment_tweets = get_negative_sentiment()['rows'][0]["value"]
    neutral_sentiment_tweets = get_neutral_sentiment()['rows'][0]["value"]
    strong_negative_sentiment_tweets = get_strong_negative_sentiment()['rows'][0]["value"]
    strong_positive_sentiment_tweets = get_strong_positive_sentiment()['rows'][0]["value"]
   
    timeline = [record["key"][0] for record in get_overall_sentiment_by_date()['rows']]
    sentiment_per_date = [math.ceil(rescaling(-1,1,0,100,record["value"]["sum"]/record["value"]["count"])) for record in get_overall_sentiment_by_date()['rows']]
    overall_sentimment_by_date = {
        'timeline': timeline,
        'sentimentPerDate': sentiment_per_date
    }

    return jsonify({
        'totalTweets': total_tweets,
        'currentSentimentOnVaccine': rescaled_overall_sentiment,
        'currentVaccinationRate': 0.013,
        'sentimentDistribution': {
            'strongNegative': strong_negative_sentiment_tweets,
            'negative': negative_sentiment_tweets,
            'neutral': neutral_sentiment_tweets,
            'positive': postive_sentiment_tweets,
            'strongPositive':strong_positive_sentiment_tweets
        },
        'overallSentimentByDate': overall_sentimment_by_date
    })

@server.route("/api/insightsDoubleClick", methods=['GET'])
def insightsDoubleClick():
    data = get_state_sentiment()
    return jsonify({
        'positive':len(list(filter(lambda score:score>50,data.values()))),
        'negative':len(list(filter(lambda score:score==50,data.values()))),
        'neutral':len(list(filter(lambda score:score<50,data.values()))),
        'totalStates': len(list(data.values()))
    })

if __name__ == '__main__':
    server.run(port=5000, debug=True,host='0.0.0.0')
