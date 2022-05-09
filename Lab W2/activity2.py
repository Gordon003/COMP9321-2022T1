import pandas as pd
from pandas.io import sql
import sqlite3

# load csv into dataframe
df = pd.read_csv('Demographic_Statistics_By_Zip_Code.csv')
df = df.sample(n = 5)

# save dataframe in sqlite database
conn = sqlite3.connect('test_database')
sql.to_sql(df, name='products', con=conn, if_exists='replace', index=False)

# Query the database and load the data into a new dataframe again
query = "SELECT * FROM products WHERE `COUNT PARTICIPANTS` > 0"
df = sql.read_sql(query, conn)
print(df)
