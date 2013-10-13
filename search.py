from login import *
from bottle import run, route

twitter_api=oauth_login()
@route('search/<query>')
def search(t, query, max_results=200, **kw):

    
    search_results = t.search.tweets(q=query, count=100, **kw)
    
    statuses = search_results['statuses']
    
    max_results = min(1000, max_results)
    
    for _ in range(10): # 10*100 = 1000
        try:
            next_results = search_results['search_metadata']['next_results']
        except KeyError, e: # No more results when next_results doesn't exist
            break
            
        # Create a dictionary from next_results, which has the following form:
        # ?max_id=313519052523986943&q=NCAA&include_entities=1
        kwargs = dict([ kv.split('=') 
                        for kv in next_results[1:].split("&") ])
        
        search_results = t.search.tweets(**kwargs)
        statuses += search_results['statuses']
        
        if len(statuses) > max_results: 
            break
            
    return statuses
    
run(host='localhost',port=8080)
q='' #enter query here


statuses=twitter_search(twitter_api, q, max_results=10)
print len(statuses)
    
    
status_texts = [ status['text'] for status in statuses ]

screen_names = [ user_mention['screen_name'] 
                    for status in statuses
                        for user_mention in status['entities']['user_mentions'] ]

hashtags = [ hashtag['text'] 
                 for status in statuses
                     for hashtag in status['entities']['hashtags'] ]

    # Compute a collection of all words from all tweets
words = [ w for t in status_texts 
              for w in t.split() ]
