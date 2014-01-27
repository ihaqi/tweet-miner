'''
import a ton of stuff

'''
from login import *
from urllib2 import URLError
from  httplib import BadStatusLine
import twitter
import json
import sys
from sys import maxint
from functools import partial
import pymongo
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def make_twitter_request(twitter_api_func, max_errors=3, *args, **kw): 
    
    # A nested helper function that handles common HTTPErrors. Return an updated 
    # value for wait_period if the problem is a 503 error. Block until the rate 
    # limit is reset if a rate limiting issue
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print >> sys.stderr, 'Too many retries. Quitting.'
            raise e
    
        # See https://dev.twitter.com/docs/error-codes-responses for common codes
    
        if e.e.code == 401:
            print >> sys.stderr, 'Encountered 401 Error (Not Authorized)'
            return None
        elif e.e.code == 404:
            print >> sys.stderr, 'Encountered 404 Error (Not Found)'
            return None
        elif e.e.code == 429: 
            print >> sys.stderr, 'Encountered 429 Error (Rate Limit Exceeded)'
            if sleep_when_rate_limited:
                print >> sys.stderr, "Sleeping for 15 minutes...ZzZ..."
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print >> sys.stderr, '...ZzZ...Awake now and trying again.'
                return 2
            else:
                raise e # Allow user to handle the rate limiting issue 
        elif e.e.code in (502, 503):
            print >> sys.stderr, 'Encountered %i Error. Will retry in %i seconds' % \
                (e.e.code, wait_period)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError, e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError, e:
            error_count += 1
            print >> sys.stderr, "URLError encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise e



        


def get_friends_or_followers_ids(twitter_api,screen_name=None,user_id=None, friends_limit=maxint, followers_limit=maxint):
	 #must have either screen_name or user_id (logical xor)

	 assert (screen_name != None) != (user_id != None)
	 "Must have screen_name or user_id but not both"

	 get_friends_ids=partial(make_twitter_request,twitter_api.friends.ids,count=5000)
	 get_followers_ids=partial(make_twitter_request,twitter_api.followers.ids,count=5000)

	 friends_ids,followers_ids=[],[]

	 for twitter_api_func, limit, ids, label in [[get_friends_ids,friends_limit,friends_ids,"friends"], [get_followers_ids, followers_limit,followers_ids,"followers"]]:
	     if limit ==0:
	         continue

	 cursor=-1

	 while cursor != 0:
	 	if screen_name:
	 		response=twitter_api_func(screen_name=screen_name,cursor=cursor)
	 	else:
	 		response=twitter_api_func(user_id=user_id,cursor=cursor)

	 	if response is not None:
	 		ids+=response['ids']
	 		cursor=response['next_cursor']

	 	print sys.stderr, 'Fetched {0} total {1} ids for {2}'.format(len(ids),label,(user_id or screen_name))

	 	if len(ids) >= limit or response is None:
	 		break
	 return friends_ids[:friends_limit], followers_ids[:followers_limit]



def harvest_user_timeline(twitter_api,screen_name=None,user_id=None, max_results=1000):

	assert(screen_name != None) != (user_id != None), \
	"Must have screen_name or user_id but not both"

	kw={ #keyword args for the Twitter API call
	'count':200,
	'trim_user': 'true',
	'include_rts':'true',
	'since_id':1	}

	if screen_name:
		kw['screen_name']=screen_name
	else:
		kw['user_id']=user_id

	max_pages=16
	results=[]

	tweets=make_twitter_request(twitter_api.statuses.user_timeline,**kw)

	if tweets is None:
		tweets=[]

	results+=tweets
	print sys.stderr, 'Fetched %i tweets' %len(tweets)
	page_num=1

	if max_results == kw['count']:
		page_num=max_pages
	while page_num < max_pages and len(tweets) >0 and len(results) <max_results:
		kw['max_id']=min([tweet['id'] for tweet in tweets])-1

		tweets=make_twitter_request(twitter_api.statuses.user_timeline, **kw)
		results+=tweets

		print sys.stderr, 'Fetched %i tweets' %(len(tweets),)
		page_num+=1

	print sys.stderr, 'Done fetching tweets'

	return results[:max_results]

def strip(date):
    return datetime.strptime(date,'%a %b %d %H:%M:%S +0000 %Y')

twitter_api=oauth_login()
tweets =harvest_user_timeline(twitter_api, screen_name='ma3route',max_results=2000)

for tweet in tweets:
    tweet['created_at']=strip(tweet['created_at'])


days_diff=(tweets[0]['created_at']-tweets[-1]['created_at']).days
last_day=tweets[0]['created_at'].date()
dct={}

for day in range(days_diff):
    tdays=[]
    td=[]
    last_day-=timedelta(1)
    for tweet in tweets:
        if tweet['created_at'].date()==last_day:
            tdays.append(tweet['created_at'])
            x=((tdays[0]-tdays[-1]).seconds)/3600.0
            td=[x]

    if td:
            dct[last_day]=td
        
        
