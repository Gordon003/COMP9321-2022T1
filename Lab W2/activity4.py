import requests
import pandas as pd

url = "https://data.cityofnewyork.us/api/views/kku6-nxdu/rows.json"

# fetch json
resp = requests.get(url=url)
json_obj = resp.json()

# # create dataframe from json
json_data = json_obj['data']

# # get column
columns = []
for c in json_obj['meta']['view']['columns']:
    columns.append(c['name'])

df = pd.DataFrame(data=json_data, columns=columns)

# # print dataframe
print("column")
print(",".join([column for column in df]))

for index, row in df.iterrows():
    print(",".join([str(row[column]) for column in df]))