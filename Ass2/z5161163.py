from flask import Flask, request, Response
from flask_restx import Resource, Api, fields, reqparse
import requests

import sqlite3
from sqlite3 import Error

from datetime import datetime as dt, timedelta

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
matplotlib.use('Agg')

import numpy as np

import re
import io

# set up api
app = Flask(__name__)
api = Api(app, version='1.0', title='z5161163 API',  description='Implementation of COMP9321 Assignment 2')
ns = api.namespace('actors', description='Finished Endpoints for Marking')
host_name = "127.0.0.1"
port_num = 5000

time_format = "%Y-%m-%d-%H:%M:%S"
day_format_lst = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]
birthday_time_format = "%Y-%m-%d"

zId = 'z5161163'

# code
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_UNPROCESSABLE_ENTITY = 422

''' sql management '''
# create/drop tables
def manage_table(conn, table_sql):
    try:
        c = conn.cursor()
        c.execute(table_sql)
    except Error as e:
        print(e)
    c.close()

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

# fetch a record
def fetch_one(conn, query_sql, insert_value):
    val = None
    try:
        c = conn.cursor()
        c.execute(query_sql, insert_value)
        val = c.fetchone()
    except Error as e:
        val = None
    finally:
        c.close()
        return val

# fetch all record
def fetch_all(conn, query_sql, insert_value):
    val = None
    try:
        c = conn.cursor()
        c.execute(query_sql, insert_value)
        val = c.fetchall()
        return val
    except Error as e:
        val = None
    finally:
        c.close()
        return val

# actor table
sql_drop_actor_table = "DROP TABLE IF EXISTS actors"
sql_create_actor_table = """
    CREATE TABLE IF NOT EXISTS actors (
        id	        INTEGER,
        ext_api_id  INTEGER UNIQUE,
        name	    TEXT,
        country     TEXT,
        birthday	TEXT,
        deathday	TEXT,
        gender	    TEXT,
        last_update TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
"""

sql_drop_actor_cast_table = "DROP TABLE IF EXISTS actors_cast"
sql_create_actor_cast_table = """
    CREATE TABLE IF NOT EXISTS "actors_cast" (
        "actorID"	INTEGER,
        "tvID"	INTEGER,
        FOREIGN KEY("tvID") REFERENCES "tv"("id"),
        FOREIGN KEY("actorID") REFERENCES "actors"("id"),
        UNIQUE("actorID", "tvID")
    );
"""

sql_drop_tv_table = "DROP TABLE IF EXISTS tv"
sql_create_tv_table = """
    CREATE TABLE IF NOT EXISTS "tv" (
        "id"	        INTEGER,
        "ext_api_id"	INTEGER UNIQUE,
        "name"	        TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
"""


''' sqlite database '''
conn = sqlite3.connect("{}.db".format(zId))

# manage_table(conn, sql_drop_actor_table)
manage_table(conn, sql_create_actor_table)
# manage_table(conn, sql_drop_actor_cast_table)
manage_table(conn, sql_create_actor_cast_table)
# manage_table(conn, sql_drop_tv_table)
manage_table(conn, sql_create_tv_table)

actor_attr = ["id", "name", "country", "birthday", "gender"]

''' parameters '''
parser_q1 = reqparse.RequestParser()
parser_q1.add_argument('name', type=str, required=True, location='values', help="Query of Actor's Name (e.g. Brad Pitt)")

parser_q5 = reqparse.RequestParser()
parser_q5.add_argument('order', type=str, default="+id",  help='How to sort page result. Must be {} with "+/-" (e.g. +birthday,-id)'.format(actor_attr))
parser_q5.add_argument('page', type=int, default=1, help="Current Page")
parser_q5.add_argument('size', type=int, default=10, help="Number of actors display in a page")
parser_q5.add_argument('filter', type=str, default="id,name", help="Actor attribute to view. Must be {} (e.g. id,birthday)".format(actor_attr))

parser_q6 = reqparse.RequestParser()
parser_q6.add_argument('format', type=str, help="Final Output. Must be [image, json]", required=True, choices=("image", "json"))
parser_q6.add_argument('by', type=str, help="Attributes to have a look at. Must be [country, birthday, gender, life_status] (e.g. country,gender)", required=True)


''' response models '''
nested_link_model = api.model('nested_link_model', {
    "href": fields.String(example = "http://{}:{}/actors/123".format(host_name, port_num))
})

nested_self_model = api.model('nested_self_model_1', {
    "self": fields.Nested(nested_link_model)
})

nested_self_model_2 = api.model('nested_self_model_2', {
    "self": fields.Nested(nested_link_model),
    "previous": fields.Nested(nested_link_model),
    "next": fields.Nested(nested_link_model)
})

nested_self_model_3 = api.model('nested_self_model_3', {
    "self": fields.Nested(nested_link_model),
    "next": fields.Nested(nested_link_model)
})

q1_model = api.model('q1_response_model', {
    "id": fields.Integer(example = 123),
    "last-update": fields.String(example = "2022-03-29-19:21:58"),
    "_links": fields.Nested(nested_self_model)
})

q2_model = api.model('q2_response_model', {
    "id": fields.Integer(example = 123),
    "last-update": fields.String(example = "2022-03-29-19:21:58"),
    "name": fields.String(example = "Bradley Cooper"),
    "country": fields.String(example = "United States"),
    "birthday": fields.String(example = "1975-01-05"),
    "deathday": fields.String(example = "null"),
    "shows": fields.List(fields.String, example=["Alias", "Limitless"]),
    "_links": fields.Nested(nested_self_model_2)
})

q3_model = api.model('q3_response_model', {
    "message": fields.String(example = "The actor with id 15 was removed from the database!"),
    "id": fields.Integer(example = 123),
})

request_schema = {
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string',
            "default": "",
        },
        'country': {
            'type': 'string',
            "default": "",
        },
        'birthday': {
            'type': 'string',
            "description": "must be in format %d-%m-%Y",
            "default": "",
        },
        'deathday': {
            'type': 'string',
            "default": "",
        },
        'shows': {
            'type': 'array',
            'items': {'type': 'string'},
            "default": [],
        },
    },
    'additionalProperties': False,
    'required': ['list'],
}
q4_request_model = api.schema_model('Q4_edit_payload', request_schema)

actor_model = api.model('actor_model', {
    "id": fields.Integer(example = 123),
    "name": fields.String(example = "Bradley Cooper"),
    "country": fields.String(example = "United States"),
    "gender": fields.String(example = "Male"),
    "birthday": fields.String(example = "1975-01-05"),
    "deathday": fields.String(example = "null"),
})

q5_model = api.model('q5_response_model', {
    "page": fields.Integer(example = 123),
    "page-size": fields.Integer(example = 123),
    "actors": fields.List(fields.Nested(actor_model)),
    "_links": fields.Nested(nested_self_model_3)
})

country_model = api.model('group_model', {
    "Australia": fields.Integer(example = 2),
    "Brazil": fields.Integer(example = 6),
    "USA": fields.Integer(example = 10),
})

gender_model = api.model('gender_model', {
    "Male": fields.Integer(example = 6),
    "Female": fields.Integer(example = 10),
})

birthday_year_model = api.model('birthday_year_model', {
    "1970-80": fields.Integer(example = 10),
    "2000-10": fields.Integer(example = 8),
})

birthday_month_model = api.model('birthday_month_model', {
    "Jan": fields.Integer(example = 10),
    "May": fields.Integer(example = 4),
    "Dec": fields.Integer(example = 8),
})


alive_model = api.model('alive_model', {
    "alive": fields.Integer(example = 100),
    "dead": fields.Integer(example = 2),
})


q6_model = api.model('q6_response_model', {
    "total": fields.Integer(example = 123),
    "total-updated": fields.Integer(example = 123),
    "by-country": fields.List(fields.Nested(country_model)),
    "by-gender": fields.List(fields.Nested(gender_model)),
    "by-birthday-year": fields.List(fields.Nested(birthday_year_model)),
    "by-birthday-month": fields.List(fields.Nested(birthday_month_model)),
    "by-life-status": fields.List(fields.Nested(alive_model))
})

error_model = api.model('error_model', {
    'timestamp': fields.String(example = "2022-03-29-19:21:58"),
    "error": fields.String(example = "Bad Request"),
    "message": fields.String(example = "Invalid Query"),
})

error_conflict_model = api.model('conflict_error_model', {
    'timestamp': fields.String(example = "2022-03-29-19:21:58"),
    "error": fields.String(example = "Conflict"),
    "message": fields.String(example = "Actors already existed in DB"),
})

resource_not_found_model = api.model('resource_not_found_model', {
    'timestamp': fields.String(example = "2022-03-29-19:21:58"),
    "error": fields.String(example = "Resource not found"),
    "message": fields.String(example = "Can't found ID in DB"),
})

def containsNumber(value):
    return any([char.isdigit() for char in value])

# get all actors
@ns.route('')
class Actors(Resource):
        
    # QUESTION 5 - DONE (CHECK)
    @api.expect(parser_q5)
    @api.response(model = q5_model, code=HTTP_OK, description="Can view all actors")
    @api.response(model = error_model, code=HTTP_BAD_REQUEST, description="Invalid Query Values")
    def get(self):
        '''Q5 - View all actors in our Sqlite DB'''

        # parse query
        args = parser_q5.parse_args()

        conn = sqlite3.connect("{}.db".format(zId))

        # record count
        sql = "SELECT count() FROM actors"
        record_count = fetch_one(conn, sql, ())[0]

        sql = ""

        column_lst = ["id", "name", "country", "birthday", "gender"]

        ''' filter '''
        filter_lst = ["id", "name"]
        if args["filter"] != None:
            clean_args = re.sub('%2C',',', args["filter"])
            filter_lst = list(map(str.lower, clean_args.split(",")))
            sql += " SELECT {} FROM actors ".format(args["filter"])
        else:
            sql += " SELECT {} FROM actors ".format(",".join(filter_lst))

        # check each filter are correct
        for filter in filter_lst:
            filter = filter.strip()
            if filter.lower() not in column_lst:
                conn.close()
                return {
                    "timestamp": dt.now().strftime(time_format),
                    "error": "Bad Request",
                    "message": "invalid parameters for filter due to unknown key"
                }, HTTP_BAD_REQUEST

        ''' size '''
        size = 10
        try:
            if args["size"] != None:
                size = int(args["size"])
        except:
            conn.close()
            return {
                "timestamp": dt.now().strftime(time_format),
                "error": "Bad Request",
                "message": "invalid parameters for size"
            }, HTTP_BAD_REQUEST

        ''' page '''
        page = 1
        if args["page"] != None:
            try:
                page = int(args["page"])
            except:
                conn.close()
                return {
                    "timestamp": dt.now().strftime(time_format),
                    "error": "Bad Request",
                    "message": "invalid parameters for page"
                }, HTTP_BAD_REQUEST

        ''' order '''
        order_href = []
        if args["order"] != None :
            sql_where_lst = []
            clean_args = re.sub("%2B","-", args["order"])
            clean_args = re.sub("%2C","+", clean_args)
            order_lst = clean_args.split(",")
            for order in order_lst:
                order = order.strip()
                if order.startswith('-'):
                    order_href.append(order)
                    sql_where_lst.append(" {} DESC ".format(order[1:]))
                    if order[1:].lower() not in column_lst:
                        conn.close()
                        return {
                            "timestamp": dt.now().strftime(time_format),
                            "error": "Bad Request",
                            "message": 'invalid order'
                        }, HTTP_BAD_REQUEST
                elif order.startswith('+'):
                    order_href.append(order)
                    sql_where_lst.append(" {} ASC ".format(order[1:]))
                    if order[1:].lower() not in column_lst:
                        conn.close()
                        return {
                            "timestamp": dt.now().strftime(time_format),
                            "error": "Bad Request",
                            "message": 'invalid order'
                        }, HTTP_BAD_REQUEST
                else:
                    conn.close()
                    return {
                        "timestamp": dt.now().strftime(time_format),
                        "error": "Bad Request",
                        "message": 'invalid order'
                    }, HTTP_BAD_REQUEST

            sql += "ORDER BY" + ",".join(sql_where_lst) + " "
        else:
            sql += "ORDER BY id ASC "

        # if no actor, return
        if record_count == 0:
            link_dict = {}
            link_dict["self"] = {
                "href": "http://{}:{}/actors?order={}&page={}&size={}&filter={}".format(host_name, port_num, ",".join(order_href), page, size, ",".join(filter_lst))
            }
            resp = {
                "page": page,
                "page-size": size,
                "actors": [],
                "_links": link_dict,
            }
            return resp, HTTP_OK

        # max
        max_limit = size * page
        min_limit = max_limit - size
        sql += "LIMIT {}".format(size * page)

        actor_resp = fetch_all(conn, sql, ())

        conn.close()

        actor_lst = []
        for actor in actor_resp[min_limit: min(max_limit, len(actor_resp))]:
            actor_lst.append( dict(zip(filter_lst, actor)))

        ''' set up link dict '''
        link_dict = {}
        link_dict["self"] = {
            "href": "http://{}:{}/actors?order={}&page={}&size={}&filter={}".format(host_name, port_num, ",".join(order_href), page, size, ",".join(filter_lst))
        }

        if page != 1 and  len(actor_lst) != 0:
            link_dict["prev"] = {
                "href": "http://{}:{}/actors?order={}&page={}&size={}&filter={}".format(host_name, port_num, ",".join(order_href), page - 1, size, ",".join(filter_lst))
            }

        if max_limit < record_count:
            link_dict["next"] = {
                "href": "http://{}:{}/actors?order={}&page={}&size={}&filter={}".format(host_name, port_num, ",".join(order_href), page + 1, size, ",".join(filter_lst))
            }

        resp = {
            "page": page,
            "page-size": size,
            "actors": actor_lst,
            "_links": link_dict,
        }
        return resp, HTTP_OK

    # QUESTION 1 - DONE (CHECK)
    @api.expect(parser_q1)
    @api.response(model = q1_model, code=HTTP_CREATED, description="Actor has been successfully added")
    @api.response(model = error_model, code=HTTP_BAD_REQUEST, description="Invalid Name Input in query")
    @api.response(model = error_conflict_model, code=HTTP_CONFLICT, description="Actor already existed in DB")
    def post(self):
        ''' Q1 - Add actors into our sqlite3 database from TVMaze API '''

        ''' parse query '''
        args = parser_q1.parse_args()
        curr_date = dt.now().strftime(time_format)

        # if can't get name in query, terminate
        if args["name"] == None or args["name"] == "":
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Name query parameter not given"
            }, HTTP_BAD_REQUEST

        # if name args contain digit, stop everything
        if containsNumber(args["name"]):
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Name must not contain any digit"
            }, HTTP_BAD_REQUEST

        # clean name query
        full_name = args["name"].lower()
        full_name = re.sub('[-.,_]', ' ', full_name)
        full_name = re.sub('[^a-z ]+', '', full_name)

        # name is empty after cleaning
        if full_name.isspace():
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Empty name query parameter"
            }, HTTP_BAD_REQUEST

        # get given name
        given_name = full_name.split()[0].strip()

        ''' call tvmaze api to get all actors '''
        external_url = "https://api.tvmaze.com/search/people?q={}".format(re.sub(' ', '+', full_name))
        response = requests.get(external_url)
        body = response.json()

        # # test check
        # print("Full Name", full_name)
        # print("given_name", given_name)
        # print("external_url", external_url)
        # print("body", body)

        ''' find first actor with same given name '''
        actor = None
        for curr_actor in body:
            temp = curr_actor["person"]["name"].lower()
            if temp.startswith(given_name):
                actor = curr_actor
                break

        # if no actor with same given name, stop everything
        if actor == None:
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Can't find any actors with same given name"
            }, HTTP_BAD_REQUEST
            
        # oscar incident
        if actor["person"]["name"] == "Will Smith":
            actor["person"]["name"] = "Will Smith - The Guy who slapped Chris Rock in the Oscar"
        elif actor["person"]["name"] == "Chris Rock":
            actor["person"]["name"] = "Chris Rock The Legend"

        # open conn to db
        conn = sqlite3.connect("{}.db".format(zId))

        # if actor already exist in db, then stop everything
        sql = ''' SELECT id FROM actors WHERE ext_api_id == ? '''
        actor_record = fetch_one(conn, sql, (actor["person"]["id"],))
        if actor_record != None:
            conn.close()
            return {
                "timestamp": curr_date,
                "error": "Conflict",
                "message": "Actor already exists in the database"
            }, HTTP_CONFLICT


        ''' add actor to actor table '''
        actor_info = actor["person"]
        actor_id = None

        # clean country info
        country = actor_info["country"]["name"] if actor_info["country"] != None else None

        # insert actor into db
        sql = ''' INSERT INTO actors(name, ext_api_id, country, birthday, deathday, gender, last_update) VALUES(?,?,?,?,?,?, ?) '''
        manage_record(conn, sql, (actor_info["name"], actor_info["id"], country, actor_info["birthday"], actor_info["deathday"], actor_info["gender"], curr_date) )
        sql = ''' SELECT id FROM actors WHERE ext_api_id == ? '''
        actor_id = int(fetch_one(conn, sql, (actor_info["id"],))[0])

        ''' call tv api to get all cast credits'''
        external_url = "https://api.tvmaze.com/people/{}/castcredits?embed=show".format(actor_info["id"])
        response = requests.get(external_url)
        body = response.json()
        
        ''' add (actor, show) to table '''
        for show in body:

            tv_info = show["_embedded"]["show"]

            # search for tv id
            sql = ''' SELECT id FROM tv WHERE ext_api_id == ? '''
            tv_record = fetch_one(conn, sql, (tv_info["id"],))
            tv_id = None
            
            # insert tv show if id doesn't exist in tv db
            if tv_record == None:
                sql = ''' INSERT INTO tv(ext_api_id, name) VALUES(?,?) '''
                manage_record(conn, sql, (tv_info["id"], tv_info["name"]))
                sql = ''' SELECT id FROM tv WHERE ext_api_id == ? '''
                tv_id = fetch_one(conn, sql, (tv_info["id"],))[0]
            else:
                tv_id = tv_record[0]

            # add (actor_id, tv_id) pair
            sql = ''' INSERT INTO actors_cast(actorID, tvID) VALUES(?,?) '''
            manage_record(conn, sql, (actor_id, tv_id,))

        # close conn to db
        conn.close()

        ''' set up response '''
        href = "http://{}:{}/actors/{}".format(host_name, port_num, actor_id)
        response = {
            "id": actor_id,
            "last-update": curr_date,
            "_links": {
                "self": {
                    "href": href
                }
            }
        }
        return response, HTTP_CREATED


# retrieve actor by its id
@ns.route('/<int:id>')
@ns.doc(params={'id': 'Actor ID in our Sqlite DB (e.g. 123)'})
class Actor(Resource):

    # QUESTION 3 - DONE (CHECKED)
    @api.response(model = q3_model, code=HTTP_OK, description="Actor has been deleted")
    @api.response(model = resource_not_found_model, code=HTTP_NOT_FOUND, description="Unable to find actor ID in DB")
    def delete(self, id):
        '''Q3 - Delete an actor from our Sqlite DB'''

        conn = sqlite3.connect("{}.db".format(zId))
        curr_date = dt.now().strftime(time_format)

        ''' check actor exists at all '''
        sql = ''' SELECT * FROM actors WHERE id == ?'''
        if fetch_one(conn, sql, (id,)) == None:
            conn.close()
            return {
                "timestamp": curr_date,
                "error": "Actor Not Found",
                "message": "Cannot find actor ID {}".format(id)
            }, HTTP_NOT_FOUND

        ''' delete from actors '''
        sql = ''' DELETE FROM actors WHERE id == ? '''
        manage_record(conn, sql, (id,))

        ''' delete from actors_cast '''
        sql = ''' DELETE FROM actors_cast WHERE actorID == ? '''
        manage_record(conn, sql, (id,))

        conn.close()

        ''' set up response'''
        response = { 
            "message" :"The actor with id {} was removed from the database!".format(id),
            "id": id
        }
        return response, HTTP_OK

    # QUESTION 2 - DONE (CHECKED)
    @api.response(model = q2_model, code=HTTP_OK, description="ID exists in DB")
    @api.response(model = error_model, code=HTTP_BAD_REQUEST, description="ID doesn't exists in DB")
    def get(self, id):
        '''Q2 - Get actor personal information from our Sqlite DB'''

        conn = sqlite3.connect("{}.db".format(zId))
        curr_date = dt.now().strftime(time_format)

        ''' get actor main info'''
        sql = ''' SELECT * FROM actors WHERE id == ? '''
        actor_record = fetch_one(conn, sql, (id,))

        # if id not in database, terminate
        if actor_record == None:
            conn.close()
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Actor ID {} can't be found.".format(id)
            }, HTTP_BAD_REQUEST

        ''' fetch all shows '''
        sql = ''' SELECT name FROM actors_cast LEFT OUTER JOIN tv ON actors_cast.tvID == tv.id WHERE actorID == ?'''
        actor_shows = [x[0] for x in fetch_all(conn, sql, (id,))]

        ''' set up link prev and next actor '''
        sql = ''' SELECT id FROM actors WHERE id > ? ORDER BY id ASC LIMIT 1'''
        next_actor = fetch_one(conn, sql, (id,))

        sql = ''' SELECT id FROM actors WHERE id < ? ORDER BY id DESC LIMIT 1'''
        prev_actor = fetch_one(conn, sql, (id,))

        conn.close()

        # set up link response
        link_dict = {}
        link_dict["self"] = {
            "href": "http://{}:{}/actors/{}".format(host_name, port_num, id)
        }

        for name, actor in [("prev", prev_actor), ("next", next_actor)]:
            if actor != None:
                link_dict[name] = {
                    "href": "http://{}:{}/actors/{}".format(host_name, port_num, actor[0])
                }


        ''' response '''
        response = {
            "id": id,
            "last-update": actor_record[7],
            "name": actor_record[2],
            "country": actor_record[3],
            "birthday": actor_record[4],
            "deathday": actor_record[5],
            "shows": actor_shows,
            "_links": link_dict,
        }

        return response, HTTP_OK

    # QUESTION 4 - DONE (CHECKED)
    @api.response(model = q1_model, code=HTTP_CREATED, description="Actor has been successfully updated in our database")
    @api.response(model = error_model, code=HTTP_BAD_REQUEST, description="Actor doesn't exist")
    @api.response(model = error_model, code=HTTP_UNPROCESSABLE_ENTITY, description="Invalid payload")
    @api.expect(q4_request_model)
    def patch(self, id):
        '''Q4 - Update an actor info in our Sqlite DB (Birthday and Deathday must be in "DD-MM-YYYY" format)'''

        conn = sqlite3.connect("{}.db".format(zId))

        payload = request.get_json()
        change_lst = []
        curr_date = dt.now().strftime(time_format)

        # check if actor id exists
        sql = ''' SELECT * FROM actors WHERE id == ? '''
        actor_record = fetch_one(conn, sql, (id,))
        if actor_record == None:
            conn.close()
            return {
                "timestamp": curr_date,
                "error": "Bad Request",
                "message": "Actor ID {} can't be found.".format(id)
            }, HTTP_BAD_REQUEST

        # check payload
        actor_attr = ["name", "country", "birthday", "deathday", "gender", "shows"]
        for key in payload:
            
            # if invalid key, terminate
            if key not in actor_attr:
                conn.close()
                return {
                    "timestamp": curr_date,
                    "error": "Bad Request",
                    "message": "invalid payload due to suspicious key"
                }, HTTP_UNPROCESSABLE_ENTITY

            val = payload[key]

            if key == "shows":
                continue

            elif val == "" or val == None or val.lower() == "null" or val.lower() == "none":
                val = None

            elif key == "birthday" or key == "deathday":
                val = None
                for curr_format in day_format_lst:
                    try:
                        val = dt.strptime(payload[key], curr_format)
                    except:
                        continue
                    break
                if val == None or val > dt.now():
                    conn.close()
                    return {
                        "timestamp": curr_date,
                        "error": "Bad Request",
                        "message": "Doesn't accept {} input".format(key)
                    },  HTTP_UNPROCESSABLE_ENTITY
                val = val.strftime(birthday_time_format)
                        
            elif key == "country":
                val = payload[key].title()

            elif key == "gender":
                val = val.title()
                if val not in ["Male", "Female"]:
                    return {
                        "timestamp": curr_date,
                        "error": "Bad Request",
                        "message": "Doesn't accept {} input".format(key)
                    },  HTTP_UNPROCESSABLE_ENTITY
            if val == None:
                change_lst.append('''{} = NULL'''.format(key))
            else:
                change_lst.append('''{} = "{}"'''.format(key, val))

        # update time
        last_updated = dt.now().strftime(time_format)
        change_lst.append('''{} = "{}"'''.format("last_update", last_updated))

        # update actor db
        sql = '''UPDATE actors SET {} WHERE id = ? '''.format(',\n'.join(change_lst))
        manage_record(conn, sql, (id, ))

        ''' tv show '''

        if "shows" in payload.keys() and len(payload[key]) > 0:

            ''' delete from actors_cast '''
            sql = ''' DELETE FROM actors_cast WHERE actorID == ? '''
            manage_record(conn, sql, (id,))

            ''' add new shows '''
            for show in payload["shows"]:

                # TODO: CHECK IF NEW SHOWS ARE ACTUALLY REAL?

                sql = ''' SELECT id FROM tv WHERE name == ? '''
                tv_record = fetch_one(conn, sql, (show,))
                tv_id = None
                
                # insert new tv into db
                if tv_record == None:
                    sql = ''' INSERT INTO tv(name) VALUES(?) '''
                    manage_record(conn, sql, (show,))
                    sql = ''' SELECT id FROM tv WHERE name == ? '''
                    tv_id = fetch_one(conn, sql, (show,))[0]
                else:
                    tv_id = tv_record[0]

                ''' add (actor, show) to table '''
                sql = ''' SELECT id FROM actors_cast WHERE actorID == ? AND tvID == ?'''
                pair_record = fetch_one(conn, sql, (id, tv_id, ))
                if pair_record == None:
                    sql = ''' INSERT INTO actors_cast(actorID, tvID) VALUES(?,?) '''
                    manage_record(conn, sql, (id, tv_id))

        conn.close()

        ''' set up response '''
        href = "http://{}:{}/actors/{}".format(host_name, port_num, id)
        response = {
            "id": id,
            "last-update": last_updated,
            "_links": {
                "self": {
                    "href": href
                }
            }
        }
        return response, HTTP_OK
        

def plot_pie(ax, title, full_dict, color=None):
    labels = full_dict.keys()
    value = [full_dict[key] for key in full_dict]

    ax.pie(value , labels=labels, autopct='%1.1f%%', startangle=90, colors = color)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title(title, fontweight='bold')
    ax.legend()

def plot_bar(ax, title, full_dict, label_size = 5):
    labels = full_dict.keys()
    value = [full_dict[key] for key in full_dict]

    ax.bar(labels, value, align='center', width=0.8, alpha=0.5)
    ax.set_title(title, fontweight='bold')
    ax.tick_params(axis="x", rotation = 30, labelsize=label_size)

def plot_barh(ax, title, full_dict, label_size = 5):
    labels = list(full_dict.keys())
    value = [full_dict[key] for key in full_dict]

    ax.barh(y=np.arange(len(labels)), width=value, tick_label=labels, alpha=0.5)
    ax.set_title(title, fontweight='bold')
    ax.tick_params(axis="y", labelsize=label_size)

# actor statistic
@ns.route('/statistics')
class ActorsStatistic(Resource):

    # QUESTION 6 [DONE]
    @api.response(model = q6_model, code=HTTP_OK, description="JSON Object or Image")
    @api.response(model = error_model, code=HTTP_BAD_REQUEST, description="Invalid query input for By")
    @api.expect(parser_q6)
    def get(self):
        ''' Q6 - Get Actor Statistic based on key attributes'''

        # parse args
        args = parser_q6.parse_args()

        # check format
        format = args["format"]
        if format not in ["image", "json"]:
            return {
                "timestamp": dt.now().strftime(time_format),
                "error": "Bad Request",
                "message": "Format not understood"
            }, HTTP_BAD_REQUEST


        conn = sqlite3.connect("{}.db".format(zId))

        ''' total & record update '''
        sql = 'select count() from actors'
        record_amount = fetch_one(conn, sql, ())[0]

        prev_day = (dt.today() - timedelta(days=1)).strftime(time_format)
        sql = 'select count() from actors where last_update > ?'
        update_amount = fetch_one(conn, sql, (prev_day,))[0]

        resp = {
            "total": record_amount,
            "total-updated": update_amount,   
        }

        ''' calculate for each "by" word '''
        actor_attr = ["country", "birthday", "gender", "life_status"]
        for by in args["by"].lower().split(","):

            by = by.strip()

            # if unknown word, terminate early
            if by not in actor_attr:
                conn.close()
                return {
                    "timestamp": dt.now().strftime(time_format),
                    "error": "Bad Request",
                    "message": "Invalid Query for By"
                }, HTTP_BAD_REQUEST

            if by == "birthday":

                sql = 'select {} from actors where birthday is not null'.format(by)
                data = fetch_all(conn, sql, ())

                year_dict = { }
                month_lst = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_dict = {x: 0 for x in month_lst }

                count = len(data)

                for x in data:
                    
                    if x[0] == None:
                        continue

                    date_object = dt.strptime(x[0], birthday_time_format)

                    year = date_object.strftime("%Y")
                    if year not in year_dict:
                        year_dict[year] = 1
                    else:
                        year_dict[year] += 1

                    month = date_object.strftime("%b")
                    month_dict[month] += 1

                year_lst = sorted(list(year_dict.keys()))
                new_year_dict = {}

                # group years by 10
                for x in year_lst:
                    val = int(x)
                    lower = val - (val % 10)
                    new_key = "{}-{}".format(lower, str(lower+9)[2:])
                    if new_key not in new_year_dict:
                        new_year_dict[new_key] = year_dict[x]
                    else:
                        new_year_dict[new_key] += year_dict[x]

                final_month_dic = {x : round(month_dict[x] / count, 2) for x in month_lst}
                final_year_dic = {x : round(new_year_dict[x] / count, 2) for x in new_year_dict}

                resp["by-{}-year".format(by)] = final_year_dic
                resp["by-{}-month".format(by)] = final_month_dic

            elif by == "life_status":

                sql = 'select count() from actors where deathday IS NULL'
                alive_count = fetch_one(conn, sql, ())[0]
                dead_count = record_amount - alive_count

                resp["by-life-status"] = {
                    "alive": round(alive_count/ record_amount, 2),
                    "dead": round(dead_count/ record_amount, 2),
                }

            else:

                group_by_dic = {}

                if by == "gender":
                    group_by_dic = {"Male": 0, "Female": 0}

                sql = 'select {}, count() from actors where {} IS NOT NULL group by {}'.format(by, by, by)
                data = fetch_all(conn, sql, ())

                temp_count = 0
                for da in data:
                    temp_count += list(da)[1]

                for da in data:
                    da = list(da)
                    group_by_dic[da[0]] = round(da[1] / temp_count, 2)

                resp["by-{}".format(by)] = group_by_dic

        if format == "json":
            return resp, HTTP_OK


        ''' MATPLOTLIB '''

        # if no actor then return text image
        if record_amount == 0:

            fig = plt.figure()
            fig.text(x = 0.3, y = 0.5, s = "No data to show due to no actors in DB")

            output = io.BytesIO()
            FigureCanvas(fig).print_png(output)
            return Response(output.getvalue(), mimetype='image/png')

        # determine row and column
        total_diagram_count = len(resp) - 1
        row = 2
        column = 1
        if total_diagram_count == 3:
            column = 2
        elif total_diagram_count == 4:
            column = 2
        elif total_diagram_count == 5:
            row = 3
            column = 2
        elif total_diagram_count == 6:
            row = 3
            column = 2
        elif total_diagram_count == 7:
            row = 4
            column = 2

        # set up matplotlib
        fig = plt.figure(figsize=(5*row, 5*column))
        plt.subplots_adjust(
            wspace=0.4, 
            hspace=0.6
        )


        count = 1
        for key in resp:

            dic = resp[key]

            if key.find("gender") != -1:

                ax = fig.add_subplot(row, column, count)
                plot_pie(ax, "Gender", dic, ['violet', 'cyan'])
                count += 1

            elif key.find("country") != -1:

                ax = fig.add_subplot(row, column, count)
                plot_barh(ax, "Country", dic, 8)
                count += 1

            elif key.find("birthday-year") != -1:

                ax = fig.add_subplot(row, column, count)
                plot_barh(ax, "Birthday Year", dic, 8)
                count += 1

            elif key.find("birthday-month") != -1:

                ax = fig.add_subplot(row, column, count)
                plot_bar(ax, "Birthday Month", dic, 7)
                count += 1
            
            elif key.find("life-status") != -1:

                ax = fig.add_subplot(row, column, count)
                plot_pie(ax, "Life Status", dic)
                count += 1

        # add amount details
        ax = fig.add_subplot(row, column, count)
        ax.axis('off')
        ax.text(x = 0, y = 0.9, s = "Main Info", fontsize = 'large', fontweight='bold')
        ax.text(x = 0, y = 0.7, s = "Total amounts of actor: {}".format(record_amount))
        ax.text(x = 0, y = 0.5, s = "Total amounts of actor last updated: {}".format(update_amount))

        # return image
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')

# run api
if __name__ == '__main__':

    app.run(host=host_name, port=port_num, debug=True)