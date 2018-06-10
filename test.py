#!/usr/bin/env python
# -*- coding: utf-8 -*-

# jarvis.py
# [YOUR NETID]

import websocket
import pickle
import json
import urllib
import requests
import sqlite3
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

import botsettings  # local .py, do not share!!

TOKEN = botsettings.API_TOKEN
DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


try:
    conn = sqlite3.connect("jarvis.db")
    c = conn.cursor()
except:
    debug_print("Can't connect to sqlite3 database...")


def post_message(message_text, channel_id):
    requests.post(
        "https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&as_user=true".format(TOKEN, channel_id,
                                                                                                 message_text))


class Jarvis():
    def __init__(self):  # initialize Jarvis
        self.JARVIS_MODE = None
        self.ACTION_NAME = None

        # SKLEARN STUFF HERE:
        self.BRAIN = None
        self.BRAIN = Pipeline([('vect', CountVectorizer()),
                               ('tfidf', TfidfTransformer()),
                               ('clf', MultinomialNB()), ])

    def on_message(self, ws, message):
        m = json.loads(message)
        debug_print(m, self.JARVIS_MODE, self.ACTION_NAME)

        # only react to Slack "messages" not from bots (me):
        if m['type'] == 'message' and 'bot_id' not in m:

            action_group = ['TIME', 'PIZZA', 'GREET', 'WEATHER', 'JOKE']
            # Normal mode
            if m['text'] == 'done' and self.JARVIS_MODE == 'Training mode':
                self.JARVIS_MODE = None
                self.ACTION_NAME = None
                training_reply_1 = 'OK, I\'m finished training'
                post_message(training_reply_1, m['channel'])
            if m['text'] == 'done' and self.JARVIS_MODE == 'Testing mode' and self.ACTION_NAME is None:
                self.JARVIS_MODE = None
                self.ACTION_NAME = None
                training_reply_2 = 'OK, I\'m finished testing'
                post_message(training_reply_2, m['channel'])
            # Training mode
            if m['text'] == 'training time' and self.JARVIS_MODE is None:
                self.JARVIS_MODE = 'Training mode'
                training_reply_3 = 'OK, I\'m ready for training. What NAME should this ACTION be?'
                post_message(training_reply_3, m['channel'])
                try:
                    c.execute("CREATE TABLE training_data (id INTEGER PRIMARY KEY ASC, txt text, action text)")
                except:
                    pass
            if self.JARVIS_MODE == 'Training mode' and self.ACTION_NAME == None and m['text'] in action_group:
                self.ACTION_NAME = m['text']
                ACTION_NAME = '`' + self.ACTION_NAME + '`'
                training_reply_4 = 'OK, let\'s call this action ' + ACTION_NAME + '. Now give me some trainning text!'
                post_message(training_reply_4, m['channel'])
            if self.JARVIS_MODE == 'Training mode' and self.ACTION_NAME is not None and m[
                'text'] not in action_group and m['text'] != 'done':
                training_reply_5 = 'OK, I\'ve got it! What else?'
                post_message(training_reply_5, m['channel'])
                # save text and action into database file
                c.execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (m['text'], self.ACTION_NAME,))
                conn.commit()  # save (commit) the changes

            # Testing mode
            if m['text'] != 'done' and self.JARVIS_MODE == 'Testing mode':
                text_list = list_get('txt')
                action_list = list_get('action')
                #               print(text_list)
                #                print(action_list)

                temp = m['text']
                print(temp)
                text_fit = self.BRAIN.fit(text_list, action_list)
                t = text_fit.predict([temp])
                print(t)
                ACTION_NAME = '`' + t[0].upper() + '`'
                training_reply_6 = 'OK, I think the action you mean is ' + ACTION_NAME + '...\
                                    Write me something else and I\'ll try to figure it out.'
                post_message(training_reply_6, m['channel'])
            if m['text'] == 'testing time' and self.JARVIS_MODE is None and self.ACTION_NAME is None:
                self.JARVIS_MODE = 'Testing mode'
                training_reply_7 = 'I\'m training my brain with the data you\'ve already given me...'
                training_reply_8 = 'OK, I\'m ready for testing. Write me something and I\'ll try to figure it out.'
                post_message(training_reply_7, m['channel'])
                post_message(training_reply_8, m['channel'])
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


# export txt and action coloums from .db file and punctuation
def list_get(s):
    #    c.execute('SELECT (txt) FROM {tn} WHERE action="{act}"'. format(tn='training_data', act = s))
    c.execute('SELECT "{cn}" FROM {tn} '.format(tn='training_data', cn=s))
    # all_rows = c.fetchall()
    result = []
    for row in c:
        temp = row[0]
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


# def bayes_fit(x,y):
#    text_clf = Pipeline([('vect', CountVectorizer()),
#                         ('tfidf', TfidfTransformer()),
#                         ('clf', MultinomialNB()),])
#    text_clf1 = text_clf.fit(x, y)
#    return(text_clf1)


r = start_rtm()
jarvis = Jarvis()
ws = websocket.WebSocketApp(r, on_message=jarvis.on_message, on_error=on_error, on_close=on_close)
ws.run_forever()


