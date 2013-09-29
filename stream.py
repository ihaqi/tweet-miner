from login import *
 
 
twitter_api=oauth_login()

twitter_stream=twitter.TwitterStream(auth=twitter_api.auth)

q=''  #enter query here


stream=twitter_stream.statuses.filter(track=q)
