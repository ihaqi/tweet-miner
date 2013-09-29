import twitter

def oauth_login():
    CONSUMER_KEY=''
    CONSUMER_SECRET=''
    OAUTH_TOKEN=''
    OAUTH_TOKEN_SECRET=''
    auth=twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    twitter_api=twitter.Twitter(auth=auth)
    return twitter_api
    

twitter_api=oauth_login()

twitter_stream=twitter.TwitterStream(auth=twitter_api.auth)

q=''  #enter query here


stream=twitter_stream.statuses.filter(track=q)
