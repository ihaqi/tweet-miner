import twitter

def oauth_login():
    CONSUMER_KEY=''
    CONSUMER_SECRET=''
    OAUTH_TOKEN=''
    OAUTH_TOKEN_SECRET=''
    auth=twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    twitter_api=twitter.Twitter(auth=auth)
    return twitter_api
    

