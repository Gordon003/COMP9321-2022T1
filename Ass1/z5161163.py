import json
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import numpy as np
import math
import re

from pyparsing import alphas

studentid = os.path.basename(sys.modules[__name__].__file__)


def log(question, output_df, other):
    print("--------------- {}----------------".format(question))

    if other is not None:
        print(question, other)
    if output_df is not None:
        df = output_df.head(5).copy(True)
        for c in df.columns:
            df[c] = df[c].apply(lambda a: a[:20] if isinstance(a, str) else a)

        df.columns = [a[:10] + "..." for a in df.columns]
        print(df.to_string())


def update_city(city_name):

    replace_dict = {
        "Tallawong": "Blacktown",
        ("Central", "Circular Quay", "Cen"): "Sydney",
        ("Mosman Bay", "Taronga Zoo"): "Mosman",
        "Olympic Park": "Sydney Olympic Park",
        "City": "Sydney",
        "Macarthur": "Campbelltown",
        "Canberra": "Acton",
        "Shark Island": "Rose Bay",
        "Newcastle Beach": "Newcastle",
        "Cockatoo Island": "Parramatta",
        "Blackwattle Bay": "Glebe",
        "Pyrmont Bay": "Pyrmont",
        "Dangar": "Dangar Island",
        ("All Saints St Peters Campus", "All Saints St Marys Campus"): "Maitland",
        "William Clarke College": "Kellyville",
        ("Maroubra Junction", "Maroubra Beach"): "Maroubra",
        "Macquarie University": "Macquarie Park",
        "Bankstown Central": "Bankstown",
        ("Belmont Depot Yard","Belmont Christian"): "Belmont",
        "All Saints": "Liverpool",
        "Bishop Druitt": "Boambee",
        ("Brigidine", "Brigidine Randwick"): "Randwick"

    }

    for key,val in replace_dict.items():
        if city_name in key: return val
    
    return city_name


def question_1(routes, suburbs):
    """
    :param routes: the path for the routes dataset
    :param suburbs: the path for the routes suburbs
    :return: df1
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    df1 = pd.read_csv(routes)

    deleted_word_lst = [
        "Station", "Stn", "City Centre", "Base Hospital", "Hospital", "CBD", "Loop", "Interchange", "Street", "Ferry",
        "College", "Public School", "PS", "HS", "Christian School", "Grammar School", "Primary", "Schools", "School", "Boys High", "Girls High", "Technology", "Grammar", "Girls", "University", "TAFE"
        "Chrisitan Community", "Christian Bros",
    ]
    regex_delete = '|'.join(deleted_word_lst)

    # clean service_direction_name
    df1["service_direction_name"] = df1.apply(lambda x: re.sub("\([a-zA-Z\s]*\)|via.*|" + regex_delete, "", x["service_direction_name"]), axis=1)
    df1["service_direction_name"] = df1.apply(lambda x: re.sub("  ", " ", x["service_direction_name"]), axis=1)

    # split into arraays
    df1["split_array"] = df1.apply(lambda x: re.findall("[A-Z][a-zA-Z]+(?:[\s-][A-Z][a-zA-Z]+)*", x["service_direction_name"]), axis=1)
    df1["start"] = df1.apply(lambda x: update_city(x["split_array"][0]), axis=1)
    df1["end"] = df1.apply(lambda x: update_city(x["split_array"][-1]), axis=1)

    log("QUESTION 1", output_df=df1[["service_direction_name", "start", "end"]], other=df1.shape)
    return df1


def question_2(df1):
    """
    :param df1: the dataframe created in question 1
    :return: dataframe df2
            Please read the assignment specs to know how to create the output dataframe
    """

    service_df = pd.Series(np.concatenate([df1["start"],df1["end"]]))
    df2 = service_df.value_counts(ascending = False).rename_axis('service_location').reset_index(name='frequency')
    df2 = df2.head(5)

    log("QUESTION 2", output_df=df2, other=df2.shape)
    return df2

def change_transport(transport_name, transport_mot):

    transport_dict = {
        1: "Train",
        2: "Metro",
        4: "Light Rail",
        5: "Bus",
        7: "Bus",
        9: "Ferry",
    }

    if transport_mot != 11: return transport_dict[transport_mot]

    transport_lst =  ["Bus", "Ferry", "Light Rail", "Train", "Metro"]
    for transport in transport_lst:
        if re.search(r"%s" % transport.lower(), transport_name, re.IGNORECASE):
            return transport

    return "None"

def question_3(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df3
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    df3 = df1.copy(True)
    df3["transport_name"] = df1.apply(lambda x: change_transport(x["transport_name"], x["mot_for_interchange_id"]), axis=1)

    log("QUESTION 3", output_df=df3[['transport_name']], other=df3.shape)
    return df3


def question_4(df3):
    """
    :param df3: the dataframe created in question 3
    :return: df4
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    df4 = df3["transport_name"].value_counts(ascending = False).rename_axis('transport_name').reset_index(name='frequency')

    log("QUESTION 4", output_df=df4[["transport_name", "frequency"]], other=df4.shape)
    return df4

def update_depot(depot_name):
    
    depot_name = depot_name.strip()

    replace_dict = {
        "Foundry Rd" : "Erskineville",
        "Bonds Rd": "Punchbowl",
        "cnr North & Harden": "Harden",
        "Percival Rd": "Stanmore"
    }

    for key,val in replace_dict.items():
        if depot_name in key: return val
    
    return depot_name


def question_5(df3, suburbs):
    """
    :param df3: the dataframe created in question 2
    :param suburbs : the path to dataset
    :return: df5
            Data Type: dataframe
            Please read the assignment specs to know how to create the output dataframe
    """
    
    df1 = pd.read_csv(suburbs)[["suburb", "state", "population"]]
    df1 = df1.drop(df1[df1["state"] != "NSW"].index)
    df1 = df1.groupby("suburb").sum().reset_index()
    df1.rename(columns={"suburb": "depot_name"} , inplace = True)
    df3["depot_name"] = df3.apply(lambda x: update_depot(re.sub("[a-zA-Z\s]*,|[0-9]||\-", "", str(x["depot_name"]))), axis=1)

    df_depot = df3["depot_name"].dropna().value_counts().rename_axis('depot_name').reset_index(name='frequency')

    df_combine = pd.merge(df_depot, df1, on='depot_name')
    df_combine["ratio"] = round(df_combine["frequency"] / df_combine["population"],3)
    df_combine = df_combine.sort_values(by=['ratio'], ascending=False).reset_index(drop = True)
    df_combine = df_combine.head(5)

    df5 = df_combine.copy(True)
    df5.rename(columns={"depot_name": "depots"}, inplace=True)
    df5 = df5.set_index('depots')

    log("QUESTION 5", output_df=df5[["ratio"]], other=df5.shape)
    return df5


def question_6(df3):
    """
    :param df3: the dataframe created in question 3
    :return: nothing, but saves the figure on the disk
    """
    table = None

    df = df3[["operator_name", "transport_name"]].copy(True)
    df['D'] = 1

    table = pd.pivot_table(df, values='D', index='operator_name', columns='transport_name', aggfunc='count', fill_value=0)

    log("QUESTION 6\n", output_df=None, other=table)
    return table

addition = 0
def plt_line(ax, name, value):
    global addition

    a = ax.barh(y = 1, width = value, left=addition)
    addition += value
    return name + "- " + str(max(round(value, 2),0.01)) + "%"

def question_7(df3,suburbs):
    """
    :param df3: the dataframe created in question 3
    :param suburbs : the path to dataset
    :return: nothing, but saves the figure on the disk
    """

    plt.figure().clear()

    global addition
    addition = 0

    # filter out suburbs that are not in greater sydney
    df1 = pd.read_csv(suburbs)
    not_sydney_lst = df1[(df1["state"] == "NSW") & (df1["statistic_area"] != "Greater Sydney")]["local_goverment_area"].unique()
    df1 = df1.drop(df1[(df1["statistic_area"] != "Greater Sydney") |  (df1["local_goverment_area"].isin(not_sydney_lst))].index)
    df1["total_income"] = df1["population"] * df1["median_income"]

    # group several suburbs in same lga
    df_group = df1.groupby(['local_goverment_area'])
    df = df_group.agg({'population': 'sum', 'sqkm': 'sum', 'median_income': 'median', 'total_income': 'sum'})
    df = df.reset_index()
    df["local_goverment_area"] =  [re.sub("\(.*\)", "", i) for i in df["local_goverment_area"]]
    df["median_total"] = df["total_income"] / df["population"]

    # set up plot
    fig = plt.figure(figsize=(12, 10))
    plt.tight_layout()
    gs = plt.GridSpec(nrows=2, ncols=2, wspace=0.4, hspace=0.4)

    # median income horizontal bar graph
    df0 = df.copy(True).sort_values(by=['median_total'], ascending=False)
    ax0 = fig.add_subplot(gs[0,0])

    ax0.set_title('Median Income', fontsize=12, fontweight='bold')
    ax0.barh(y = np.arange(len(df0)), width=df0["median_total"], height = 0.6, tick_label=df0["local_goverment_area"], color='green')
    
    ax0.tick_params(axis='x', labelsize=6)
    ax0.set_xlabel("AUD")

    ax0.tick_params(axis='y', labelsize=6)
    ax0.set_ylabel("LGA of Greater Sydney")


    # population vs population density horizontal bar graph
    ax1 = fig.add_subplot(gs[0,1])
    ax2 = ax1.twiny()
    df1 = df.copy(True).sort_values(by=['population'], ascending=False)
    df1["population_density"] = df1["population"] / df1["sqkm"]
    Y_AXIS = np.arange(df1.shape[0])

    ax1.set_title('Population', fontsize=12, fontweight='bold')
    
    color1 = 'dodgerblue'
    ax1.barh(y = Y_AXIS - 0.2, width=df1["population"], height=0.4, color=color1, tick_label=df1["local_goverment_area"], alpha=0.8)
    ax1.tick_params(axis="x", colors=color1, labelsize=6)
    ax1.set_xlabel("# of people", color=color1)

    ax1.tick_params(axis='y', labelsize=6)
    ax1.set_ylabel("LGA of Greater Sydney")

    color2 = 'darkorange'
    ax2.barh(y = Y_AXIS + 0.2, width=df1["population_density"], height=0.4, color=color2, tick_label=df1["local_goverment_area"], alpha=0.8)
    ax2.tick_params(axis="x", colors=color2, labelsize=6)
    ax2.set_xlabel("# of people / sqkm", color=color2)

    # Area Distribution
    ax3 = fig.add_subplot(gs[1,:])
    df3 = df.copy(True).sort_values(by=['sqkm'], ascending=False)
    df3["percentage"] = df3["sqkm"] / df3["sqkm"].sum()
    df3["title"] = df3.apply(lambda rec: plt_line(ax3, rec["local_goverment_area"], rec["percentage"]), axis = 1)

    ax3.set_title('LGA Area Distribution of NSW (Sqkm)', fontsize=12, fontweight="bold")
    ax3.axis('off')

    ax3.legend(df3["title"], loc="lower left", ncol=5, prop={'size': 8})

    # plt.show()
    plt.savefig("{}-Q7.png".format(studentid))

def plot_line_text(coord_list, plt, x, y, start, end):


    if ((x, y) in coord_list) or start == end:
        return
        
    change = [-0.2,-0.1,0,0.1,0.2]

    for xchange in change:
        for ychange in change:
            coord_list.append((x+xchange,y+ychange))

    a = plt.text(x = x,y= y, s = start + "-" + end, fontsize = 4)

def question_8(df3,suburbs):
    """
    :param df3: the dataframe created in question 3
    :param suburbs : the path to dataset
    :return: nothing, but saves the figure on the disk
    """

    # set up plot
    plt.figure().clear()
    plt.xlabel("Latitiude (Degrees)")
    plt.ylabel("Longitude (Degrees)")

    # clean suburbs df
    df1 = pd.read_csv(suburbs)
    df1 = df1.drop(df1[(df1["state"] != "NSW") | (df1["lng"] > 155)].index)
    df1["size"] = (df1["sqkm"] / df1["sqkm"].max()) * 50

    transport_dict = {
        "Train": "orange",
        "Ferry": "green",
        "Light Rail": "red",
        "Metro": "blue"
    }

    # plot suburbs with transport
    df_route = df3[df3["transport_name"].isin(transport_dict.keys())][["start", "end", "transport_name"]]
    unique_city_set = set(list(df_route["start"].unique()) + list(df_route["end"].unique()))
    df_unique_city = df1[df1["suburb"].isin(unique_city_set)]

     # plot the whole suburbs but in very low alpha
    df_whole = df1[(df1['lng'] >= df_unique_city['lng'].min()) & (df1['lng'] <= df_unique_city['lng'].max()) & (df1['lat'] <= df_unique_city['lat'].max()) & (df1['lat'] >= df_unique_city['lat'].min())]
    plt.scatter(x=df_whole['lng'], y=df_whole['lat'], c=df_whole["sqkm"], cmap='hot', s = df_whole["size"], alpha=0.1, label="suburb")
    plt.scatter(x=df_unique_city['lng'], y=df_unique_city['lat'], c=df_unique_city["sqkm"], cmap='hot', s = df_unique_city["size"], alpha=0.8)

    # iterate through each transport method
    coord_list = []
    for transport in transport_dict.keys():

        # get route with that transport method
        df2 = df3[df3["transport_name"] == transport][["start", "end"]]

        # get lat and long of start and end
        df_suburbs = df1[["suburb", "lat", "lng"]]
        df_start = df_suburbs.rename(columns={"lat": "start_lat", "lng": "start_lng"})
        df2 = pd.merge(df2, df_start, how='left', left_on='start', right_on='suburb')
        df_end = df_suburbs.rename(columns={"lat": "end_lat", "lng": "end_lng"})
        df2 = pd.merge(df2, df_end, how='left', left_on='end', right_on='suburb')

        # drop route that has no lat and lng
        df2 = df2.dropna(subset=['start_lng', 'end_lng', 'start_lat', 'end_lat'])

        # plot line,text and legend
        df2.apply(lambda row: plt.plot([row['start_lng'], row['end_lng']], [row['start_lat'], row['end_lat']], linewidth=0.5, color=transport_dict[transport], alpha=0.8), axis=1)
        df2.apply(lambda row: plot_line_text(coord_list, plt, round((row['start_lng'] + row['end_lng']) / 2, 1), round((row['start_lat'] + row['end_lat']) / 2 , 1), row['start'], row['end']), axis=1)
        plt.plot([], [], color=transport_dict[transport], label=transport)

    plt.legend()
    plt.savefig("{}-Q8.png".format(studentid), dpi=1000)


if __name__ == "__main__":
    df1 = question_1("routes.csv", "suburbs.csv")
    df2 = question_2(df1.copy(True))
    df3 = question_3(df1.copy(True))
    df4 = question_4(df3.copy(True))
    df5 = question_5(df3.copy(True), "suburbs.csv")
    table = question_6(df3.copy(True))
    question_7(df3.copy(True), "suburbs.csv")
    question_8(df3.copy(True), "suburbs.csv")
    