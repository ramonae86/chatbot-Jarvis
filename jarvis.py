#!/usr/bin/env python
# -*- coding: utf-8 -*-

# jarvis.py
# [YOUR NETID]

import sys
import websocket
import pickle
import json
import urllib
import requests
import sqlite3
import re
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
# FILL IN ANY OTHER SKLEARN IMPORTS ONLY

import botsettings # local .py, do not share!!
TOKEN = botsettings.API_TOKEN
DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


try:
    conn = sqlite3.connect("jarvis.db")
    c = conn.cursor()
    # c.execute("DROP TABLE training_data")
    # c.execute("CREATE TABLE training_data (id INTEGER PRIMARY KEY ASC, txt text, action text)")
    # conn.commit()
except:
    debug_print("Can't connect to sqlite3 database...")


def post_message(message_text, channel_id):
    requests.post("https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&as_user=true".format(TOKEN,channel_id,message_text))


class Jarvis():
    
    def __init__(self): # initialize Jarvis
        self.JARVIS_MODE = None
        self.ACTION_NAME = None
        
        # SKLEARN STUFF HERE:
        self.BRAIN = None # FILL THIS IN

        # timeList = list_get('TIME')
        # pizzaList = list_get('PIZZA')
        # GREET_list = list_get('GREET')
        # WEATHER_list = list_get('WEATHER')
        # JOKE_list = list_get('JOKE')
        # print(pizzaList)
        # print(test_vec(pizzaList).shape)

    def on_message(self, ws, message):
        m = json.loads(message)
        debug_print(m['text'], self.JARVIS_MODE, self.ACTION_NAME)
        # only react to Slack "messages" not from bots (me):
        if m['type'] == 'message' and 'bot_id' not in m:
            # for row in c.execute("SELECT * from training_data"):
            #     print(row)
            if self.JARVIS_MODE == 'training' and m['text'].lower() == 'done':
                self.JARVIS_MODE = None
                self.ACTION_NAME = None
                post_message('OK, I\'m finished training.', m['channel'])
            if self.ACTION_NAME is not None and self.JARVIS_MODE == 'training':
                c.execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (m['text'], self.ACTION_NAME,))
                conn.commit()
                post_message('OK, I\'ve got it! What else?', m['channel'])
            if self.ACTION_NAME is None and self.JARVIS_MODE == 'training':
                self.ACTION_NAME = m['text'].upper()
                response = 'OK, let\'s call this action `' + m['text'].upper() + '`. Now give me some training text!'
                post_message(response, m['channel'])
            if self.JARVIS_MODE is None and m['text'].lower() == 'training time':
                self.JARVIS_MODE = 'training'
                try:
                    c.execute("CREATE TABLE training_data (id INTEGER PRIMARY KEY ASC, txt text, action text)")
                except:
                    pass
                post_message('OK, I\'m ready for training. What NAME should this ACTION be?', m['channel'])

            # testing mode

            if m['text'] != 'done' and self.JARVIS_MODE == 'Testing':
                text_list = list_get('txt')
                action_list = list_get('action')
                #               print(text_list)
                #                print(action_list)

                temp = m['text']
                print(temp)
                text_fit = bayes_fit(text_list, action_list)
                t = text_fit.predict(temp)
                print(t)
                ACTION_NAME = '`' + t.upper + '`'
                training_reply_6 = 'OK, I think the action you mean is ' + ACTION_NAME + '...\
                                                Write me something else and I\'ll try to figure it out.'
                post_message(training_reply_6, m['channel'])
            if m['text'] == 'testing time' and self.JARVIS_MODE is None and self.ACTION_NAME is None:
                self.JARVIS_MODE = 'Testing'
                reply = 'I\'m training my brain with the data you\'ve already given me...\
                        \nOK, I\'m ready for testing. Write me something and I\'ll try to figure it out.'
                post_message(reply, m['channel'])
        pass


def start_rtm():
    """Connect to Slack and initiate websocket handshake"""
    r = requests.get("https://slack.com/api/rtm.start?token={}".format(TOKEN), verify=False)
    r = r.json()
    r = r["url"]
    return r


def on_error(ws, error):
    print("SOME ERROR HAS HAPPENED", error)


def on_close(ws):
    conn.close()
    print("Web and Database connections closed")


def on_open(ws):
    print("Connection Started - Ready to have fun on Slack!")


# def list_get(s):
#     c.execute('SELECT (txt) FROM training_data WHERE action="{act}"'. format(act=s))
#     # all_rows = c.fetchall()
#     result = []
#     for row in c:
#         temp = row[0]
#         result.append(temp)
#     return result

def list_get(s):
#    c.execute('SELECT (txt) FROM {tn} WHERE action="{act}"'. format(tn='training_data', act = s))
    c.execute('SELECT "{cn}" FROM {tn} '. format(tn='training_data', cn = s))
    #all_rows = c.fetchall()
    result = []
    for row in c:
        temp=row[0]
        result.append(temp)
    punctuation = '!"$%&`()*+,-./;<=>?[\]^_`{|}~“”—'
    text_list = ["none"] * len(result)
    for i in range(len(result)):
        text_list[i] = result[i]
        exclude = set(punctuation)  # Keep a set of "bad" characters.
        list_noPunct = [char for char in text_list[i] if char not in exclude]
        list_lower = [word.lower() for word in list_noPunct]
        list_words = "".join(list_lower)
        result[i] = list_words
    return result

def test_vec(stringList):
    cleanList = []
    for line in stringList:
        letterOnly = re.sub("[^a-zA-Z]", " ", line)
        words = letterOnly.lower().split()
        text = " ".join(words)
        cleanList.append(text)

    vectorizer = CountVectorizer(analyzer="word", tokenizer=None, preprocessor=None, stop_words='english')
    listFeatures = vectorizer.fit_transform(cleanList)
    return listFeatures


def bayes_fit(x, y):
    text_clf = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', MultinomialNB()), ])
    text_clf1 = text_clf.fit(x, y)
    return text_clf1


r = start_rtm()
jarvis = Jarvis()
ws = websocket.WebSocketApp(r, on_message=jarvis.on_message, on_error=on_error, on_close=on_close)
ws.run_forever()


