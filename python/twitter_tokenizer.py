# -*- coding: utf-8 -*-

"""<
#This code file follows the SLiP (Semi-Literate Programming) annotation convention.
#specification at: ...
title:      "Twitter tokenizer and sentiment analysis"
author:     Roy Prins
published:  17-04-2014
status:     project
progress:   80
summary: >
    Tokenizing tweets.
>"""

"""<
#Tokenizing twitter

Dit is de uitleg helpt het als ik een zit vol tik, of maa Dit is de uitleg helpt het als ik een zit vol tik, of maa
Dit is de uitleg helpt het als ik een zit vol tik, of maa
Dit is de uitleg helpt het als ik een zit vol tik, of maaDit is de uitleg helpt het als ik een zit vol tik, of maa

##tweede kop

>"""

from HTMLParser import HTMLParser
import regex as re
import nltk
import csv


p_URL = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
p_EMOTICON = ur"""
    ツ | ☹ | ☺ | ♥ | ㋡ | ♡ |    # Single character emoticons / emoji's
    <3 |                         # Alternate
    (?:                          # Sideways facial expressions :-))
        [<>]?
        [:;=8X]                         # - eyes
        [\-o\*\']?                      # - optional nose
        [\)\]\(\[dDpPOo/\:\}\{@\|\\]+   # - mouth
        |
        [\)\]\(\[dDpPOo/\:\}\{@\|\\]+   # - mouth
        [\-o\*\']?                      # - optional nose
        [:;=8]                          # - eyes
        [<>]?
    ) |
    (?:                          # Upright facial expressions (^_^)
        [\({]?                          # - optional left circumference
        [\-\^\*><OoXx@0]                # - left eye
        [_\.o]                          # - mouth / nose
        [\-\^\*><OoXx@0]                # - right eye
        [\)}]?                          # - optional right circumference
    )
    """
p_HANDLE = r'(?:@[\w_]{1,15})'
p_HASHTAG = r"""(?:\#+[\w_]+[\w\'_\-]*[\w_]+)"""
p_WORD = ur"[\p{L}][\p{L}'’\-*]+"


#functions
def f_EMOTICON(t):
    """limit character sequence to 2: :-)))) > :-))"""
    return re.sub(r'(.)\1{2,}', r'\1\1', t)

def f_HANDLE(t):
    return t.lower()

def f_HASHTAG(t):
    """retain ALLCAPS else lowercase: #BAD > #BAD,   #Bad > #bad"""
    return t if t.upper() == t else t.lower()

def f_WORD(t):
    """ - retain ALLCAPS else lowercase: BAD > BAD,   Bad > bad
        - limit character sequence to 3: coooool > coool"""
    t = t if t.upper() == t else t.lower()
    return re.sub(r'(.)\1{3,}', r'\1\1\1', t)

#lexer rules have a name, pattern (token recognition) and a function (postprocessing)
lexrules = [
    ("URL",       p_URL,      None),
    ("EMOTICON",  p_EMOTICON, f_EMOTICON),
    ("HANDLE",    p_HANDLE,   f_HANDLE),
    ("HASHTAG",   p_HASHTAG,  f_HASHTAG),
    ("WORD",      p_WORD,     f_WORD),
]

#commonly used words that do not ususally tranfer sentiment
stopwords = ("the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he",
             "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
             "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about",
             "who", "get", "which", "go", "me", "when", "make", "can", "time", "no", "just", "him", "know", "take",
             "people", "into", "year", "your", "could", "them", "see", "other", "than", "then", "now", "look",
             "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "first", "am",
             "way", "even", "because", "any", "these", "day", "most", "us", "got", "is", "are", "i'm", "im",
             "here", "it's", "had", "was", "while", "we're")



def lex(text, rules=lexrules):
    """lexer that returns only the recognized tokens"""
    #remove &quot; and other html stuff
    text = HTMLParser().unescape(text)
    regexp = re.compile("|".join(["(?P<%s>%s)" % (n, p) for n, p, f in rules]), re.VERBOSE | re.UNICODE)
    tokens = []
    for match in regexp.finditer(text):
        for name, pattern, func in rules:
            tok = match.group(name)
            if tok is not None:
                if func:
                    tok = func(tok)
                #eliminate stopwords
                if name == 'WORD' and tok in stopwords:
                    break
                tokens.append((name, tok))
    return tokens

test_batch = (
    ('positive', 'excited',
u"@stellargirl I loooooooovvvvvveee my #Kindle2. Not that the DX is cool, but the 2 is fantastic in its own right."),
    ('negative', 'excited',
u"is upset that he can't update his Facebook by texting it... and might cry \as a result School today also. Blah!"),
    ('positive', 'excited',
u"im meeting up with one of my besties tonight! &lt;3 Cant wait!!  - GIRL TALK"),
    ('positive', 'excited',
u"I am so jealous, hope you had a great time in vegas! how did you like the ACM's?! ♡♡ LOVE YOUR SHOW!!"),
    ('negative', 'excited',
u"NOOOOOOO my DVR just died and I was only half way through the EA presser. Hate you Time Warner #FML"),
    ('negative', 'excited',
u"F*ck Time Warner Cable!!! You f*cking suck balls!!! I have a $700 HD tv &amp; my damn HD channels hardly ever come in. Bullshit!!"),
    ('positive', 'excited',
u"at James house eatin nice and delicious food :) http://dummylink.com"),
    ('positive', 'excited',
u"today is my Happy day coz, im goin to BaLi !  it sounds exciting!"),
    ('negative', 'subdued',
u"yup, my cat is still stranded  she's just sitting on the table, sleeping, waiting for the rain to pass"),
    ('negative', 'subdued',
u"Aside from the apps store disparity, I see little reason to pick a current iPhone over Pre. We'll see after tmrw though")
)


def get_tokens(text):
    """return a list of only the WORD and EMOTICON-type tokens"""
    return [token for name, token in lex(text) if name in ('WORD', 'EMOTICON')]


def get_all_tokens(batch):
    """return a flat list of WORD and EMOTICON tokens for a labeled batch"""
    tokens = []
    for v, a, text in batch:
        tokens.extend(get_tokens(text))
    return tokens


with open('traindata.csv', 'rU') as csvfile:
    reader = csv.reader(csvfile, dialect='excel',)
    next(reader, None)  # skip header
    training_batch = []
    for v, a, text in reader:
        training_batch.append((v, a, unicode(text, "utf-8")))


frequency_dist = nltk.FreqDist(get_all_tokens(training_batch))

def extract_features(tokens):
    """match the frequency distribution to a list of tokens"""
    tokens = set(tokens)
    features = {}
    for tok in frequency_dist.keys():
        features['contains(%s)' % tok] = (tok in tokens)
    return features


def label_features(batch, label):
    """return a list of features + label for a given label
    0 for valence, 1 for arousal"""
    labellist = []
    for row in batch:
        labellist.append((get_tokens(row[2]), row[label]))
    return labellist


valence_training_set = nltk.classify.apply_features(extract_features, label_features(training_batch, 0))
arousal_training_set = nltk.classify.apply_features(extract_features, label_features(training_batch, 1))

valence_test_set = nltk.classify.apply_features(extract_features, label_features(test_batch, 0))
arousal_test_set = nltk.classify.apply_features(extract_features, label_features(test_batch, 1))

valence_classifier = nltk.NaiveBayesClassifier.train(valence_training_set)
arousal_classifier = nltk.NaiveBayesClassifier.train(arousal_training_set)





if __name__=="__main__":
    print("DEMONSTRATION OF THE LEXER ON THE FIRST 3 TEST TWEETS:\n")
    for v, a, text in test_batch[:3]:
        print("= "*40)
        print(text)
        print("- "*40)
        for token in lex(text):
            print('%s: %s') % (token[0], token[1])

    print("\n\nMOST INFORMATIVE FEATURES, VALENCE + AROUSAL:")
    valence_classifier.show_most_informative_features(5)
    arousal_classifier.show_most_informative_features(5)

    print("\n\nACCURACY SCORE ON TEST SET:")
    print("Valence accuracy: %s") % nltk.classify.accuracy(valence_classifier, valence_test_set)
    print("Arousal accuracy: %s") % nltk.classify.accuracy(arousal_classifier, arousal_test_set)

    print("\n\nDEMONSTRATION OF THE CLASSIFIER ON THE FIRST 3 TEST TWEETS:\n")
    for v, a, text in test_batch[:3]:
        print("= "*40)
        print(text)
        print("valence: %s | classifier: %s") % (v, valence_classifier.classify(extract_features(get_tokens(text))))
        print("arousal: %s | classifier: %s") % (a, arousal_classifier.classify(extract_features(get_tokens(text))))


    print("\n\nMOVIE REVIEWS:\n")

    """<


    Movies                       | positive    | excited
    ---------------------------- | ----------- | -------------
    watched #12YearsASlave       | 72%         | 84%
    watched #DallasBuyersClub    | 85%         | 79%
    watched #Nebraska            | 93%         | 86%
    paint dry                    | 35%         | 8%





    Dream jobs                  | positive    | excited
    --------------------------- | ----------- | ------------
    politician                  | 23%         | 78%
    president                   | 76%         | 45%
    doctor                      | 62%         | 54%
    nurse                       | 71%         | 73%
    dentist                     | 29%         | 75%
    teacher                     | 63%         | 69%
    waitress                    | 43%         | 66%
    stewardess                  | 77%         | 77%
    pilot                       | 40%         | 71%
    fireman                     | 59%         | 58%
    policeman                   | 74%         | 65%
    writer                      | 53%         | 49%
    journalist                  | 55%         | 70%
    artist                      | 65%         | 72%
    singer                      | 89%         | 79%
    actor                       | 87%         | 38%
    pornstar                    | 69%         | 85%
    athlete                     | 64%         | 65%
    cashier                     | 57%         | 68%
    programmer                  | 54%         | 54%
    web developer               | 88%         | 16%

    >"""

    from TwitterSearch import *

    #twitter api credentials hidden in separate file for obvious reasons
    with open('twitterapi.txt', 'rb') as f:
        consumer_key, consumer_secret, access_key, access_secret = f.read().splitlines()

    review_limit = 100

    subjects = [
        ['apples'],
        ['oranges']
    ]

    for keywords in subjects:
        positive_count = 0
        excited_count = 0
        review_count = 0

        try:
            tso = TwitterSearchOrder() # create a TwitterSearchOrder object
            tso.setKeywords(keywords)
            tso.setLanguage('en')
            tso.setCount(review_limit) # 15 results per page
            tso.setIncludeEntities(False)

            ts = TwitterSearch(consumer_key, consumer_secret, access_key, access_secret)

            response = ts.searchTweets(tso)
            for status in response['content']['statuses']:
                review_count += 1
                if valence_classifier.classify(extract_features(get_tokens(status['text']))) == 'positive':
                    positive_count += 1
                if arousal_classifier.classify(extract_features(get_tokens(status['text']))) == 'excited':
                    excited_count += 1

            print(keywords)
            if review_count > 0:
                print('positive: %s' % ((positive_count*100.0)/review_count))
                print('excited: %s' % ((excited_count*100.0)/review_count))
            else:
                print('no results, try another search entry')
        except TwitterSearchException as e:
            print(e)



"""<
#References

+ [A simple lexer in Python,  Eli Golovinsky](http://www.gooli.org/blog/a-simple-lexer-in-python/)
+ [Twitter sentiment analysis using Python and NLTK, Laurent Luce](http://www.laurentluce.com/posts/twitter-sentiment-analysis-using-python-and-nltk/)
+ [Natural Language Processing with Python, chapter 6: Learning to classify text](http://www.nltk.org/book/ch06.html)
+ [Sentiment Symposium Tutorial: Tokenizing, Christopher Potts](http://sentiment.christopherpotts.net/tokenizing.html)
+ [Exploiting Emoticons in Sentiment Analysis, Alexander Hogenboom et al.](http://eprints.eemcs.utwente.nl/23268/01/sac13-senticon.pdf)
+ [Alex Davies' website](http://alexdavies.net/twitter-sentiment-analysis/)
+ [Enhanced Sentiment Learning Using Twitter Hashtags and Smileys, Dmitry Davidov et al.](http://oldsite.aclweb.org/anthology-new/C/C10/C10-2028.pdf)
+ [Visualizing twitter sentiment, Healey & Ramaswamy](http://www.csc.ncsu.edu/faculty/healey/tweet_viz/)
+ [Recognising Emotions and Sentiments in Text, Sunghwan Mac Kim](http://sydney.edu.au/engineering/latte/docs/11-Kim-Master_Thesis_Final.pdf)
>"""