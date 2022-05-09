import pandas as pd

# read csv into dataframe
df = pd.read_csv('Demographic_Statistics_By_Zip_Code.csv')
df = df.sample(n = 5)

# df column
df_columns = df.keys().to_list()
print(",".join(df_columns))

# df row
for index, row in df.iterrows():
    print(",".join([str(row[column]) for column in df]))

# save dataframe as csv
file_name = "edited_version.csv"
df.to_csv(file_name, sep=",", encoding='utf-8', index=False)
