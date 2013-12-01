from login import *
import re
from bottle import run, route, template, post, get, request, static_file

import pymongo
import csv

connection = pymongo.Connection("localhost", 27017)
db = connection.sentiment

t=oauth_login()

@route('/')
def home():
    return template('home')

@get('/<filename:re:.*\.js>')
def javascripts(filename):
    return static_file(filename, root='static/js')

@get('/<filename:re:.*\.css>')
def stylesheets(filename):
    return static_file(filename, root='static/css')

@route('/twitter_stream/<query>')
def twitter_stream(query):
    twitter_stream=twitter.TwitterStream(auth=t.auth)
    qstream=twitter_stream.statuses.filter(track=query)

    for tweet in qstream:
        if tweet.get('text'):
            print "Fetching Tweets..."
            if tweet['lang']=='en':
                tweet['query']=query
                db.sentiment.save(tweet)
                

    return template('query',{'query':query})

@post('/query')
def get_query():
    query=request.forms.get('query')
    if(query==None or query==""):
        query="No query selected."

    return template('query',{'query':query})


def get_training_data():
    '''Get the training data from the the input file.
    Return a list of [[label,tweet]] for each tweet in the training set.
    The tweet part is a list of words in the tweet.
    e.g. ['positive', ['happy', 'birthday', 'the', 'fantabulously', '@shrimponbarbie']] 
    '''
    f=open('mejajsenti1.csv','rb')  #training file
    reader=csv.reader(f,delimiter=',')
    training_data = []  #list that will hold the training tweets
    for row in reader:  #loop through the entire file
        training_data.append(row)   # add each label, tweet pair to the list
    
    training_data=[item for item in training_data if len(item)==2] #ensure that each item in the set is of length 2
    
    for i in range(len(training_data)-1): #loop through entire training set         
        if not isinstance(training_data[i][1],list): #check whether tweet part of training set is a list
        #turn the tweet into a list of words in lower case for words that have a length of at least 3
        #lower case words makes comparison easier so that 'good' and 'Good' are taken as the same word
        #checking word length ensures that words such as 'a', 'an', 'is', 'be' etc. are eliminated from
        #the pool of words and may not add any value
            training_data[i][1]=[word.lower() for word in training_data[i][1].split()]
        
    
    f.close()
    
    return training_data
    


def get_test_data_from_file():
    '''Get test data from input file.
    Return a list of tweets for each tweet in the training set.
    The tweet is itself a list of words in the tweet.
    e.g. ['the', '@nysenate', 'floor', 'should', 'more', 'festive', 'bright', 'and',
     'glittery.', 'congratulations,', 'ny!']
    '''
    f=open('mejajtest.csv','rb')
    reader=csv.reader(f,delimiter=',')
    test_data = []  #list to store the data
    for row in reader:
        test_data.append(row)
    
    for i in range(len(test_data)-1): #loop through entire training set
        if not isinstance(test_data[i][1],list): #check whether tweet part of training set is a list
        #turn the tweet into a list of words in lower case
                test_data[i][1]=[word.lower() for word in test_data[i][1].split()]
        
    f.close()
    
    return test_data


def get_tweets_from_db(query):
    query=query
    tweets=db.sentiment.find({'query':query})
    test=[]

    for tweet in tweets:
        test.append(['',tweet['text'].encode('utf-8')])


    for i in range(len(test)-1): #loop through entire training set
        if not isinstance(test[i][1],list): #check whether tweet part of training set is a list
        #turn the tweet into a list of words in lower case
                test[i][1]=[word.lower() for word in test[i][1].split()]     

    return test


def get_words(data):
    '''
    Get the words in the training/test set.
    Returns a list of the unique words(vocabulary) in the data
    '''
    words = []  #list to hold all the words in the
    for item in data:
        words.extend(item[1])
    return list(set(words))

# Get Probability of each word in the training data
# If label is specified, find the probability of each word in the corresponding labelled tweets only
def get_word_prob(training_data, label = None):
    '''
    Get the probability of each word in the training/test data.
    The label is optional.
    Returns a dictionary with key, value pairs of word and probability
    '''
    words = get_words(training_data)    #list of all unique words in the set
    freq = {}   #dictionary to store frequency of each word in the set

    for word in words:
        freq[word] = 1  #initialize count of each unique word to 1

    total_count = 0     #variable to store the count of all words 
    for data in training_data:
        if data[0] == label or label == None:
            total_count += len(data[1]) #increment word count for each word
            for word in data[1]:    #loop through every word in tweet part of training data
                freq[word] += 1     #increment count of each word in tweet for each tweet

    prob = {}   #dictionary to store the probability of each word in the set
    for word in freq.keys():
        prob[word] = freq[word]*1.0/total_count #calculate probability of each word

    return prob


def get_label_prob(training_data, label):
    '''Get the probability for a given label
    Returns the probability value for each label as per the training set
    '''
    label_count = 0
    total_count = 0
    for data in training_data:
        total_count += 1    #increment total stepwise
        if data[0] == label:
            label_count += 1    #increment label count stepwise
    return label_count*1.0/total_count

# Label the test data given the trained parameters Using Naive Bayes Model
def label_data(test_data, positive_word_prob, negative_word_prob, positive_prob, negative_prob):
    labels = []
    count={}
    count['positive']=0
    count['negative']=0
    for data in test_data:
        data_prob_positive = positive_prob
        data_prob_negative = negative_prob
        
        for word in data[1]:
            if word in positive_word_prob:
                data_prob_positive *= positive_word_prob[word]
                data_prob_negative *= negative_word_prob[word]
            else:
                continue

        if data_prob_positive >= data_prob_negative:
            labels.append([' '.join(data[1]), 'positive', data_prob_positive, data_prob_negative])
            count['positive']+=1
        else:
            labels.append([' '.join(data[1]), 'negative', data_prob_positive, data_prob_negative])
            count['negative']+=1
    pos='pos: '+str(count['positive'])
    neg='neg: '+str(count['negative'])
    nulist=[pos,neg,count['positive'],count['negative']]
    return labels

# Print the labelled test data

def print_labelled_data(labels):
    f_out = open('test_labelled', 'w')
    for [tweet, label, prob_positive, prob_negative] in labels:
        f_out.write('%s %s\n' % (tweet, label))

    f_out.close()
    

@route('/show/<files>')
def show_final(files):
    files=files
    fil=open(files,'r')
    tweets=[]

    for f in fil.readlines():
        #f=f.strip()
        dets=f.split()
        twt=dets[:-1]
        snt=dets[-1]
        #twt=twt.decode('utf-8','replace')
        tweets.append([twt,snt])

    return template('classify',labels=tweets)

@route('/classify/<query>')
def classify(query):
    query=query
    # Get the training and test data
    training_data = get_training_data()
    #test_data = get_test_data_from_file()
    test_data=get_tweets_from_db(query)
    # Get the probabilities of each word overall and in the two labels
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

    # Label the test data and print it
    test_labels = label_data(test_data, positive_word_prob, negative_word_prob, positive_prob, negative_prob)
    print_labelled_data(test_labels)

    right=0
    wrong=0
    dict1={}
    dict2={}
    fyl=open('inaccurate.txt','w')
    for i in range(len(test_data)-1):
        dict1[' '.join(test_data[i][1])]=test_data[i][0]

    for i in range(len(test_labels)-1):
        dict2[test_labels[i][0]]=test_labels[i][1]

    for key in dict2.keys():
        if dict2[key]==dict1[key]:
            right+=1
        else:        
            wrong+=1
            acc=str(key)+" "+str(dict2[key])+" "+str(dict1[key])
            fyl.write(acc+"\n")

    total=right+wrong
    accuracy=right/float(total)
    print "Accuracy: ", accuracy

    return template('show')


run(host='localhost', port=8000, debug=True)
