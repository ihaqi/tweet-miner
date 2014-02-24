'''
import a ton of stuff

'''
from login import *
from classifier import *
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

def get_user_retweets(tweets):
    user_retweets=0
    for tweet in tweets:
        if tweet.has_key('retweeted_status'):
            user_retweets+=1
    return user_retweets



def get_user_mentions(tweets):
    screen_names=[user_mention['screen_name'] 
                    for status in tweets
                        for user_mention in status['entities']['user_mentions']]
    
    return len(set(screen_names))
    
def get_hashtags(tweets):
    hashtags=[hashtag['text']
                for tweet in tweets
                    for hashtag in tweet['entities']['hashtags']]
    
    return len(set(hashtags))

def get_urls(tweets):
    urls=[url['expanded_url']
            for tweet in tweets
                for url in tweet['entities']['urls']]
                
    return len(set(urls))

def get_symbols(tweets):
    symbols=[symbol['text']
                for tweet in tweets
                    for symbol in tweet['entities']['symbols']]
    
    return len(set(symbols))
    
def get_media(tweets):
    media=[]
    for tweet in tweets:
        if tweet['entities'].has_key('media'):
            media.append(tweet['entities']['media'][0]['url'])
    
  
    return len(set(media))

def create_matrix(tweets):
    hashtags=get_hashtags(tweets)
    media=get_media(tweets)
    urls=get_urls(tweets)
    symbols=get_symbols(tweets)
    mentions=get_user_mentions(tweets)
    retweets=get_user_retweets(tweets)
    total_tweets=len(tweets)
    test_data = get_test_tweets(tweets)
    test_labels = label_data(test_data, positive_word_prob, negative_word_prob, positive_prob, negative_prob)
    #print test_labels
    pos=test_labels[0]
    neg=test_labels[1]
    matrix=[pos,neg,hashtags,media,urls,symbols,retweets,mentions,total_tweets]
    
    
    return matrix

def create_dataframe(init,fin,labels,timestamp):
     df=pd.DataFrame(data={'init':init,'fin':fin},columns=['init','fin'],index=labels)
     df.columns.name=timestamp
     return df
#def get_matrix(tweets):

if __name__=="__main__":
    tweet_rate=3600
    abs_index=0                
    twitter_api=oauth_login()
    tweets =harvest_user_timeline(twitter_api, screen_name='winmitch',max_results=400)
    tweets.reverse()
    labels=['positive','negaitve','hashtags','media','urls','symbols','retweets','mentions','total_tweets']
    #twt_dct=tweets_dict(tweets=tweets)
    for tweet in tweets:
        tweet['created_at']=strip(tweet['created_at'])
        
    training_data = get_training_data()
    
   
    word_prob = get_word_prob(training_data)
    positive_word_prob = get_word_prob(training_data, 'positive')
    negative_word_prob = get_word_prob(training_data, 'negative')

    # Get the probability of each label
    positive_prob = get_label_prob(training_data, 'positive')
    negative_prob = get_label_prob(training_data, 'negative')

    # Normalise for stop words
    for (word, prob) in word_prob.iteritems():
        positive_word_prob[word] /= prob
        negative_word_prob[word] /= prob
    i=0
    j=0
    final_matrix=None
    #k=0
    while i < (len(tweets)-2):
        i+=1
        #print i
        time_diff=(tweets[i]['created_at']-tweets[i-1]['created_at']).total_seconds()
        #print i,time_diff, tweets[i]['created_at']
        if time_diff>(2*tweet_rate):
            
            if final_matrix == None:
                initial_matrix=create_matrix([])
                #print initial_matrix
                final_matrix=create_matrix(tweets[j:i])
                #print final_matrix
                df=create_dataframe(initial_matrix,final_matrix,labels,tweets[i]['created_at'])
                print df
                j=i
                #print j
            else:
                #print i, time_diff
                initial_matrix=final_matrix
                final_matrix=create_matrix(tweets[j:i])
                #print i,j,initial_matrix,final_matrix,abs_index,tweet_rate
                j=i
            if abs_index==0:
                abs_index=time_diff
                #print abs_index
            else:
                abs_index=(abs_index+time_diff)/2
                #print abs_index
            
        else:
            tweet_rate=(tweet_rate+time_diff)/2
            #print abs_index, tweet_rate
                
