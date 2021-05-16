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

class DupCount(CouchView):
    map = '''
    function (doc) {
      emit(doc['id_str'], 1);
    }
    '''

    reduce = '''
        _count
    '''

class CountTotal(CouchView):

    map = '''
    function (doc) {
        emit(doc['country'], 1);
    }
    '''

    reduce = '''
        _sum
    '''


class CitySentiments(CouchView):

    map = '''
    function (doc) {
        emit(doc['location'], doc['polarity']);
    }   
    '''

    reduce = '''
        _stats
        '''


class OverallSentiments(CouchView):

    map = '''
    function (doc) {
        emit(doc['country'], doc['polarity']);
    }
    '''
    reduce = '''
        _stats
    '''


class PositiveSentimentPerCity(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] > 0 && doc['polarity'] < 0.5) {
            emit(doc['location'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class NegativeSentimentPerCity(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] < 0 && doc['polarity'] > -0.5) {
            emit(doc['location'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''
class StrongNegativeSentimentPerCity(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] <= -0.5) {
            emit(doc['location'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''

class StrongPositiveSentimentPerCity(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] >= 0.5) {
            emit(doc['location'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class NeutralSentimentPerCity(CouchView):
    """ Count the number of documents available, per type. """
    map = '''
    function (doc) {
        if (doc['polarity'] == 0) {
            emit(doc['location'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class SentiByCityAndDate(CouchView):

    map = '''
    function (doc) {
        emit([doc['date'], doc['state'],doc['city']], doc['polarity']);
    }     
    '''

    reduce = '''
        function (keys, values, rereduce) {
          if (rereduce) {
            return sum(values);
          } else {
            return sum(values);
          }
        }
    '''