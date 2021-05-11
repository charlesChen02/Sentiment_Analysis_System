from couchdb import Server

from couchview import CouchView
import couchdb

'''
Reminder: structure of JSON
{"created_at": "Sun May 02 11:24:52 +0000 2021", 
"text": "@im_riya0 I am Bangladeshi. If you are a Bangladeshi you should not bother who is ruling India.  It's not our busin\u2026 https://t.co/e0vCRhip9Q", 
"timestamp_ms": "1619954692968", 
"location": "Adelaide, South Australia", 
"country": "Australia", 
"bounding_box": {"xmin": 138.44213, "ymin": -35.34897, "xmax": 138.78019, "ymax": -34.652564}, 
"sentiment": {"polarity": 0.0, "subjectivity": 0.0}}

'''


class CountTypes(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'country' in doc:
            yield doc['country'], 1

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)


class CountSentiments(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'city' in doc and 'polarity' in doc:
            yield doc['city'], doc['polarity']

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)


class OverallSentiments(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'country' in doc and 'polarity' in doc:
            yield doc['country'], doc['polarity']

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)


class PositiveSentimentPerCity(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'city' in doc and 'polarity' in doc and doc['polarity'] > 0:
            yield doc['city'], 1

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)


class NegativeSentimentPerCity(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'city' in doc and 'polarity' in doc and doc['polarity'] < 0:
            yield doc['city'], 1

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)


class NeutrarlSentimentPerCity(CouchView):
    """ Count the number of documents available, per type. """

    @staticmethod
    def map(doc):
        """ Emit the document type for each document. """
        if 'city' in doc and 'polarity' in doc and doc['polarity'] == 0:
            yield doc['city'], 1

    @staticmethod
    def reduce(keys, values, rereduce):
        """ Sum the values for each type. """
        return sum(values)