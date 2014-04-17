import urllib
import httplib2
import json
import twitter
import credentials
import re
import argparse
import datetime
import time
import logging
from bs4 import BeautifulSoup
#from nltk.corpus import stopwords
#import feedparser
#import nltk
#import pytumblr
#from PIL import Image
from urllib2 import urlopen
import io
from random import choice, randint

try:
    from file_locations_prod import *
except ImportError:
    pass
try:
    from file_locations_dev import *
except ImportError:
    pass

API_QUERY = 'http://api.trove.nla.gov.au/result?q={keywords}&zone={zone}&key={key}&encoding=json&n={number}&s={start}'
ALCHEMY_KEYWORD_QUERY = 'http://access.alchemyapi.com/calls/url/URLGetRankedKeywords?url={url}&apikey={key}&maxRetrieve=10&outputMode=json&keywordExtractMode=strict'
ZONES = ['book', 'article', 'picture', 'sound', 'collection', 'map']

FORMATS = {
    'artwork': (['Art work'], 'picture', None),
    'article': (None, 'article', None),
    'chapter': (['Article/Book chapter'], 'article', None),
    'paper': (['Article/Conference paper'], 'article', None),
    'report': (['Article/Report'], 'article', None),
    'review': (['Article/Review'], 'article', None),
    'book': (None, 'book', None),
    'proceedings': (['Conference Proceedings'], 'book', None),
    'data': (['Data set'], 'article', None),
    'map': (None, 'map', None),
    'object': (['Object'], 'picture', None),
    'periodical': ([
        'Periodical',
        'Periodical/Journal, magazine, other',
        'Periodical/Newspaper'
        ], 'article', None),
    'photo': (['Photograph'], 'picture', None),
    'picture': (None, 'picture', None),
    'poster': (['Poster, chart, other'], 'picture', None),
    'archives': (None, 'collection', None),
    'score': (['Printed music'], 'music', None),
    'sound': (None, 'music', None),
    'interview': (['Sound/Interview, lecture, talk'], 'music', None),
    'music': (['Sound/Recorded music'], 'music', None),
    'thesis': (['Thesis'], 'book', None),
    'video': ([
        'Video'
        ], 'music'),
    'abcrn': (None, 'music', 'ABC:RN')
}

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,)


def lock():
    with open(LOCK_FILE, 'w') as lock_file:
        lock_file.write('1')
    return True


def unlock():
    with open(LOCK_FILE, 'w') as lock_file:
        lock_file.write('0')
    return True


def is_unlocked():
    with open(LOCK_FILE, 'r') as lock_file:
        if lock_file.read().strip() == '0':
            return True
        else:
            return False


def get_api_result(query):
    h = httplib2.Http()
    resp, content = h.request(query)
    try:
        json_data = json.loads(content)
    except ValueError:
        json_data = None
    return json_data


def get_start(query, zone, facets, aus, online):
    url = format_url(query, zone, facets, aus, online)
    #print url
    json_data = get_api_result(url)
    try:
        total = int(json_data['response']['zone'][0]['records']['total'])
    except (KeyError, TypeError):
        total = 0
    #print total
    return randint(0, total)


def extract_date(text):
    if re.search(r'\b\d{4}\b', text):
        year = re.search(r'(\b\d{4}\b)', text).group(1)
        text = re.sub(r'\b\d{4}\b', 'date:[{0} TO {0}]'.format(year), text)
    return text


def extract_params(query):
    if '#any' in query:
        query = query.replace('#any', '')
        query = '({})'.format(' OR '.join(query.split()))


def extract_title(url):
    h = httplib2.Http()
    query = None
    try:
        resp, content = h.request(url)
        soup = BeautifulSoup(content)
        if soup.find('h1'):
            query = soup.find('h1').string.strip()
        elif soup.find('meta', name=re.compile('title')):
            query = soup.find('meta', attrs={'name': re.compile('title')})['content'].strip()
        elif soup.find('title'):
            query = soup.find('title').string.strip()
    except httplib2.ServerNotFoundError:
        return None
    return query


def check_trove_newspapers(url):
    print url
    is_trove = False
    patterns = [
        'http://trove.nla.gov.au/ndp/del/article',
        'http://nla.gov.au/nla.news-article'
    ]
    for pattern in patterns:
        if pattern in url:
            is_trove = True
            break
    return is_trove


def get_alchemy_result(query_url, xpath=None):
    if check_trove_newspapers(query_url) == True:
        xpath = '//div[@class="ocr-text"]/p' 
    h = httplib2.Http()
    url = ALCHEMY_KEYWORD_QUERY.format(
        key=credentials.alchemy_api,
        url=urllib.quote_plus(query_url)
    )
    if xpath:
        url += '&sourceText=xpath'
        url += '&xpath={}'.format(urllib.quote_plus(xpath))
    resp, content = h.request(url)
    results = json.loads(content)
    #print results
    return results


def extract_url_keywords(tweet, text, xpath=None):
    query = None
    keywords = []
    try:
        if tweet.urls[0].expanded_url:
            url = tweet.urls[0].expanded_url
        else:
            url = tweet.urls[0].url
    except (IndexError, NameError):
        return None
    else:
        # Use Alchemy
        results = get_alchemy_result(url)
        for keyword in results['keywords']:
            value = keyword['text']
            if len(value.split()) > 1:
                keywords.append('"{}"'.format(value.encode('utf-8')))
            else:
                keywords.append(value.encode('utf-8'))
    query = '({})'.format(' OR '.join(keywords))
    print query
    return query


def get_zone_results(query, aus, online):
    zones = []
    url = format_url(query, ','.join(ZONES), None, aus=aus, online=online)
    json_data = get_api_result(url)
    print json_data
    for zone in json_data['response']['zone']:
        try:
            total = int(zone['records']['total'])
            if total > 0: 
                zones.append(zone['name'])
        except (KeyError, TypeError):
            pass
    return zones


def get_zone(query, format, aus, online):
    zone = None
    facets = None
    nuc = None
    if format:
        facets = FORMATS[format][0]
        zone = FORMATS[format][1]
        nuc = FORMATS[format][2]
    elif query:
        zones = get_zone_results(query, aus, online)
        zone = choice(zones)
    else:
        format = choice(FORMATS.keys())
        facets = FORMATS[format][0]
        zone = FORMATS[format][1]
    return (zone, facets, nuc)


def get_format(text):
    format = None
    for tag in FORMATS.keys():
        hashtag = '#{}'.format(tag)
        if hashtag in text:
            format = tag
            text = text.replace(hashtag, '').strip()
            break
    return (text, format)


def process_tweet(tweet):
    query = None
    random = False
    aus = False
    online = False
    text = tweet.text.strip()
    user = tweet.user.screen_name
    text = text[10:].replace(u'\u201c', '"').replace(u'\u201d', '"').replace(u'\u2019', "'")
    #print text
    text, format = get_format(text)
    #print format
    if '#luckydip' in text:
        # Get a random article
        text = text.replace('#luckydip', '').strip()
        random = True
    if '#aus' in text:
        text = text.replace('#aus', '').strip()
        aus = True
    if '#online' in text:
        text = text.replace('#online', '').strip()
        online = True
    if '#any' in text:
        text = text.replace('#any', '').strip()
        #print "'{}'".format(query)
        query = '({})'.format(' OR '.join(text.split()))
    if not query:
        query = extract_url_keywords(tweet, text)
    if not query:
        query = extract_date(text)
    if not query:
        random = True
    zone, facets, nuc = get_zone(query, format, aus, online)
    #print zone
    if nuc:
        if query:
            query += ' nuc:"{}"'.format(nuc)
        else:
            query = 'nuc:"{}"'.format(nuc)
    if not query:
        query = ' '

    record = get_record(zone, facets, query, aus, online, random)
    if not record:
        if query and not query == ' ':
            # Search failed
            chars = 100 - len(user)
            message = "@{user} BOT IS SORRY! No article matching '{text}'.".format(user=user, text=text[:chars])
        else:
            # Something's wrong, let's just give up.
            message = "@{user} BOT HAS FAILED! Something went wrong. [:-(] {date}".format(user=user, date=datetime.datetime.now())
    else:
        url = record['troveUrl']
        title = record['title']
        chars = 118 - (len(user) + 5)
        title = title[:chars]
        message = "@{user} '{title}' {url}".format(user=user, title=title.encode('utf-8'), url=url)
    return message


def format_url(query, zone, facets, aus, online, start=0, number=0):
    url = API_QUERY.format(
        keywords=urllib.quote_plus(query),
        key=credentials.api_key,
        zone=zone,
        start=start,
        number=number
    )
    if facets:
        for facet in facets:
            url += '&l-format={}'.format(urllib.quote_plus(facet))
    if aus:
        url += '&l-australian=y'
    if online:
        url += '&l-availability=y%2Ff'
    return url


def get_record(zone, facets, query=' ', aus=False, online=False, random=False):
    if random:
        if zone == 'article' and query == ' ' and not facets:
            start = randint(0, 10000000)
        else:
            start = get_start(query, zone, facets, aus, online)
    else:
        start = 0
    url = format_url(query, zone, facets, aus, online, number=1, start=start)
    print url
    json_data = get_api_result(url)
    try:
        record = json_data['response']['zone'][0]['records']['work'][0]
    except (KeyError, IndexError, TypeError):
        return None
    else:
        return record


def tweet_reply(api):
    if is_unlocked():
        lock()
        message = None
        with open(LAST_ID, 'r') as last_id_file:
            last_id = int(last_id_file.read().strip())
        #print api.VerifyCredentials()
        try:
            results = api.GetMentions(since_id=last_id)
        except:
            logging.exception('{}: Got exception on retrieving tweets'.format(datetime.datetime.now()))
        else:
            for tweet in results:
                if tweet.in_reply_to_screen_name == 'TroveBot':
                    #print tweet.text
                    try:
                        message = process_tweet(tweet)
                    except:
                        logging.exception('{}: Got exception on process_tweet'.format(datetime.datetime.now()))
                        message = None
                    if message:
                        try:
                            print message
                            api.PostUpdate(message, in_reply_to_status_id=tweet.id)
                        except:
                            logging.exception('{}: Got exception on sending tweet'.format(datetime.datetime.now()))
                    time.sleep(20)
            if results:
                with open(LAST_ID, 'w') as last_id_file:
                    last_id_file.write(str(max([x.id for x in results])))
        finally:
            unlock()


def tweet_random(api):
    zone, facets = get_zone('', None, aus=True, online=False)
    try:
        record = get_record(zone, facets, aus=True, random=True)
        url = record['troveUrl']
    except TypeError:
        logging.exception('{}: Got exception on tweet_random'.format(datetime.datetime.now()))
    else:
        chars = 114
        title = record['title'][:chars]
        message = "'{title}' {url}".format(title=title.encode('utf-8'), url=url)
        print message
        api.PostUpdate(message)


if __name__ == '__main__':
    api = twitter.Api(
        consumer_key=credentials.consumer_key,
        consumer_secret=credentials.consumer_secret,
        access_token_key=credentials.access_token_key,
        access_token_secret=credentials.access_token_secret
    )
    parser = argparse.ArgumentParser()
    parser.add_argument('task')
    args = parser.parse_args()
    if args.task == 'reply':
        tweet_reply(api)
    elif args.task == 'random':
        tweet_random(api)

