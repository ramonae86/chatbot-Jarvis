#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# build_db.py
# Jim Bagrow
# Last Modified: 2016-08-03

import sys, os
import sqlite3

if __name__ == '__main__':
    
    db_file = "jarvis.db"
    
    # if os.path.exists(db_file):
    #     sys.exit("db already exists, exiting...")
        # You can just trash the db file if you need to.
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # questions table, and some fake data:
    c.execute("CREATE TABLE training_data (id INTEGER PRIMARY KEY ASC, txt text, action text)")
    
    msg_txt = "What time is it?"
    action = "TIME"
    c.execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (msg_txt, action,))
    
    conn.commit() # save (commit) the changes
    
    # how to select existing data
    for row in c.execute("SELECT * from training_data"):
        print(row)

    # clear out the table so it's ready for YOUR data:
    c.execute("DELETE FROM training_data")
    # close it up:
    conn.close()

    # try:
    #     os.remove('jarvis.db')
    #     print('database file removed!')
    # except:
    #     print('some error occurred')
