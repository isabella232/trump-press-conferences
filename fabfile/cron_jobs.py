#!/usr/bin/env python

"""
Cron jobs
"""

import logging

from datetime import datetime
from fabric.api import execute, local, require, task

import app_config
import copytext
import json
import os
import pytz
import twitter

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@task
def publish_json():
    execute('text.update')
    tweet_count = 0
    currentID = 0
    
    last_conf_date, last_conf_endtime = read_spreadsheet()
    utc_time = create_utc_time(last_conf_date, last_conf_endtime)
    number_of_tweets, lastID = get_trump_tweets(utc_time, currentID, tweet_count)

    with open('data/data.json', 'w') as f:
        data = {
            'last_conf_date': last_conf_date,
            'last_conf_endtime': last_conf_endtime,
            'number_of_tweets': number_of_tweets,
            'lastID': lastID
        }

        json.dump(data, f)

    local('aws s3 cp data/data.json s3://%s/%s/data/ --acl public-read --cache-control max-age=5' % (app_config.S3_BUCKET, app_config.GRAPHIC_SLUG))


def read_spreadsheet():
    COPY = copytext.Copy(app_config.COPY_PATH)
    last_conf_date = COPY['data']['last_conf_date']['value']
    last_conf_endtime = COPY['data']['last_conf_endtime']['value']

    return last_conf_date, last_conf_endtime

def get_trump_tweets(utc_time, currentID, tweet_count):

    api = twitter.Api(consumer_key=os.environ['TRUMP_TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TRUMP_TWITTER_CONSUMER_SECRET'],
        access_token_key=os.environ['TRUMP_TWITTER_ACCESS_KEY'],
        access_token_secret=os.environ['TRUMP_TWITTER_ACCESS_SECRET']
    )

    params = {
        'screen_name': 'realDonaldTrump',
        'count': 200,
        'trim_user': True
    }

    if currentID > 0:
        params['max_id'] = currentID

    trump_tweets = api.GetUserTimeline(**params)

    for tweet in trump_tweets:
        tweet_datetime = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
        utc = pytz.timezone('UTC')
        utc_tweet_datetime = utc.localize(tweet_datetime, is_dst=None)

        if utc_time > utc_tweet_datetime:
            return tweet_count, currentID

        currentID = tweet.id
        tweet_count += 1

    return get_trump_tweets(utc_time, currentID, tweet_count)



def create_utc_time(date, time):
    month, day, year = date.split('/')
    hour, everything_else = time.split(':')

    month = month.zfill(2)
    day = day.zfill(2)
    
    if len(year) < 4:
        year = '20%s' % year

    hour = hour.zfill(2)


    est = pytz.timezone('US/Eastern')
    full_datetime = '%s/%s/%s %s:%s' % (month, day, year, hour, everything_else)
    print(full_datetime)

    parsed = datetime.strptime(full_datetime, '%m/%d/%Y %I:%M %p')
    with_timezone = est.localize(parsed, is_dst=None)
    utc = with_timezone.astimezone(pytz.utc)


    return utc

@task
def test():
    """
    Example cron task. Note we use "local" instead of "run"
    because this will run on the server.
    """
    require('settings', provided_by=['production', 'staging'])

    local('echo $DEPLOYMENT_TARGET > /tmp/cron_test.txt')