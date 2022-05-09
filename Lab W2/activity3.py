import json
import pandas as pd
from pymongo import MongoClient

# load csv into dataframe
df = pd.read_csv('Demographic_Statistics_By_Zip_Code.csv')
df = df.sample(n=1)

db_name = 'comp9321'
mongo_port = 27017
mongo_host = 'localhost'
collection = 'Demographic_Statistics'

# create mongodb db
client = MongoClient(host=mongo_host, port=mongo_port)
db = client[db_name]
c = db[collection]

# write df in mongodb
data = df.to_dict(orient='records')
c.insert_many(data)

# query db
client = MongoClient(host=mongo_host, port=mongo_port)
db = client[db_name]
c = db[collection]

# load data into new df
df_new = pd.DataFrame(list(c.find()))

