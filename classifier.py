
import csv


def get_training_data():
    '''Get the training data from the the input file.
    Return a list of [[label,tweet]] for each tweet in the training set.
    The tweet part is a list of words in the tweet.
    e.g. ['positive', ['happy', 'birthday', 'the', 'fantabulously', '@shrimponbarbie']] 
    '''
    f=open('train.csv','rb')  #training file
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
    




def get_test_tweets(tweets):
    
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
    nulist=[count['positive'],count['negative']]
    return nulist


    





