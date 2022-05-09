import os
import json

import sqlite3
from sqlite3 import Error

from datetime import datetime as dt


# insert/delete record
def manage_record(conn, insert_sql, insert_value):
    try:
        c = conn.cursor()
        c.execute(insert_sql, insert_value)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        c.close()

your_path = 'data'
files = os.listdir(your_path)

conn = sqlite3.connect('z5161163.db')

sql = ''' DELETE from ACTORS'''
manage_record(conn, sql, ())

for file in files:

    f = open("{}/{}".format(your_path,file))
    data = json.load(f)

    for actor in data:

        actor_info = actor["person"]

        country = None
        if actor_info["country"] != None:
            country = actor_info["country"]["name"]

        last_updated = dt.now().strftime("%Y-%m-%d-%H:%M:%S")

        sql = ''' INSERT INTO actors(name, ext_api_id, country, birthday, deathday, gender, last_update) VALUES(?,?,?,?,?,?,?) '''
        manage_record(conn, sql, (actor_info["name"], actor_info["id"], country, actor_info["birthday"], actor_info["deathday"], actor_info["gender"],last_updated,) )

conn.close()