import sys
import pandas as pd
import csv
import numpy as np
# import time

from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_regression, f_classif
from sklearn.linear_model import Ridge, RidgeClassifier
from sklearn.metrics import mean_squared_error, precision_score, accuracy_score, recall_score, average_precision_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

# start_time = time.time()

np.seterr(divide='ignore', invalid='ignore')

ZID = "z5161163"

def convert_exp_to_str(exp_num):
    value=str(exp_num)
    value2=value.replace(',', '.')
    return str(round(float(value2),2))

# encode categorical variable to numerical value
def hot_encode(dataset):
    for (var, dtype) in zip(dataset.columns, dataset.dtypes):
        if dtype == "object":
            dummies = pd.get_dummies(dataset[var], prefix=var)
            dataset = dataset.drop(columns=var).merge(dummies,left_index=True,right_index=True)
    return dataset

''' get file link from command line '''
training_file_link = sys.argv[1]
test_file_link = sys.argv[2]

''' open csv file '''
df_train = pd.read_csv(training_file_link).drop(columns="SK_ID_CURR")

df_test = pd.read_csv(test_file_link)
id_test = df_test["SK_ID_CURR"]

''' remove data with low variance and covariance '''

# drop lst
col_lst = [
    "FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_WORK_PHONE", "FLAG_CONT_MOBILE", "FLAG_PHONE", "FLAG_EMAIL",
    "REG_REGION_NOT_LIVE_REGION", "REG_REGION_NOT_WORK_REGION", "LIVE_REGION_NOT_WORK_REGION", "REG_CITY_NOT_LIVE_CITY",
    "REG_CITY_NOT_WORK_CITY", "LIVE_CITY_NOT_WORK_CITY", "DAYS_LAST_PHONE_CHANGE"
]
df_train = df_train.drop(columns=col_lst)

# low covaraince with target
doc_list = ["FLAG_DOCUMENT_{}".format(x) for x in range(2, 22)]
df_train = df_train.drop(columns=doc_list)

''' hot encode categorical variable '''
df_train = hot_encode(df_train)
df_test = hot_encode(df_test)

''' fill in null value '''
df_train = df_train.fillna(df_train.mean())
df_test = df_test.fillna(df_test.mean())

''' resize X_test to meet X_train columns '''
test_row_count = df_test.shape[0]
for col in df_train.columns:
    if col not in df_test.columns:
        new_pd = pd.DataFrame({col: [0] * test_row_count})
        df_test = pd.concat(objs=[df_test, new_pd], axis=1)
df_test = df_test[df_train.columns]


''' QUESTION 1 - REGRESSION '''

# split x and y dataset
y_column = "AMT_INCOME_TOTAL"
X_train = df_train.loc[:, df_train.columns != y_column]
y_train = df_train[y_column]
X_test = df_test.loc[:, df_test.columns != y_column]
y_test = df_test[y_column]

''' model setup '''

X_train_q1 = X_train.copy()
X_test_q1 = X_test.copy()

# drop feature
drop_lst = [
    "AMT_GOODS_PRICE", "LANDAREA_AVG", "FLOORSMAX_MODE"
]
X_train_q1 = X_train_q1.drop(columns=drop_lst)
X_test_q1 = X_test_q1.drop(columns=drop_lst)

# pipeline
scaler = StandardScaler().fit(X_train_q1)
featureSelect = SelectKBest(score_func=f_regression)
model = Ridge()

pipe = Pipeline(
    steps=[
        ('featureSelect', featureSelect),
        ('scaler', scaler),
        ('model', model)
    ]
)


parameters = dict(
    featureSelect__k = [150],
    model__alpha =  [0.7]
)

clf = GridSearchCV(
    estimator = pipe,
    param_grid = parameters
)

clf.fit(X_train_q1, y_train)

''' prediction '''
y_pred = clf.predict(X_test_q1)

''' evaluation '''
# mse
mse = mean_squared_error(y_test, y_pred)
mse = convert_exp_to_str(mse)

# correlation
y_pred = pd.Series(y_pred)
# corr = y_test.corr(y_pred)
corr, _ = pearsonr(y_test, y_pred)
corr = convert_exp_to_str(corr)

# print("QUESTION 1")
# print("mse: {}".format(mse))
# print("corr: {}".format(corr))

''' write csv file '''
# q1 summary
csv_file = "{}.PART1.summary.csv".format(ZID)
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["zid","MSE","correlation"])
    writer.writerow([ZID, mse, corr])

# q1 output
csv_file = "{}.PART1.output.csv".format(ZID)
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["SK_ID_CURR","predicted_income"])
    for id, income in zip(id_test, y_pred):
        writer.writerow([id, round(income, 2)])

''' QUESTION 2 - CLASSIFICATION '''

# split x and y dataset
y_column = "TARGET"
X_train = df_train.loc[:, df_train.columns != y_column]
y_train = df_train[y_column]
X_test = df_test.loc[:, df_test.columns != y_column]
y_test = df_test[y_column]

''' model setup '''

X_train_q2 = X_train.copy()
X_test_q2 = X_test.copy()

# drop feature
drop_lst = []
X_train_q2 = X_train_q2.drop(columns=drop_lst)
X_test_q2 = X_test_q2.drop(columns=drop_lst)

# pipeline
scaler = StandardScaler().fit(X_train_q2)
featureSelect = SelectKBest(score_func=f_classif)
model = RidgeClassifier()

pipe = Pipeline(
    steps=[
        ('featureSelect', featureSelect),
        ('scaler', scaler),
        ('model', model)
    ]
)

parameters = dict(
    featureSelect__k = [80],
    model__alpha =  [0.7]
)

clf = GridSearchCV(
    estimator = pipe,
    param_grid = parameters
)

clf.fit(X_train_q2, y_train)

''' evaluation '''
y_pred = clf.predict(X_test)

precision = average_precision_score(y_test, y_pred, average='macro')
precision = convert_exp_to_str(precision)

recall = recall_score(y_test, y_pred, average='macro')
recall = convert_exp_to_str(recall)

accuracy = accuracy_score(y_test, y_pred)
accuracy = convert_exp_to_str(accuracy)

# print("QUESTION 2")
# print("precision:\t", precision)
# print("recall:\t\t", recall)
# print("accuracy:\t", accuracy)


''' write csv file '''
# q2 summary
csv_file = "{}.PART2.summary.csv".format(ZID)
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["zid","average_precision","average_recall","accuracy"])
    writer.writerow([ZID, precision, recall, accuracy])

# q2 output
csv_file = "{}.PART2.output.csv".format(ZID)
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["SK_ID_CURR","predicted_target"])
    for id, target in zip(id_test, y_pred):
        writer.writerow([id, target])
        
# print("--- %s seconds ---" % (time.time() - start_time))