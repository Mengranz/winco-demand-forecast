#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import csv
import pandas as pd
import numpy as np
import time
from datetime import datetime
from datetime import timedelta

# take sys agrv
from sys import argv
from tqdm import tqdm
ITEM_START = argv[1]
ITEM_END = argv[2]


def ma(lead, alpha, past_order, inv, on_the_way):
    return int(lead*alpha* np.mean(past_order)) - inv - on_the_way


def simulator_date(table, alpha, window, func, LEAD=12, INIT_AMOUNT=0, pr=True):
   
    LEAD_WEEK = timedelta(days = 7*LEAD)
    
    if INIT_AMOUNT == 0:
        INIT_AMOUNT = np.mean(table["OrderQty"]) * LEAD * 1.2  #buffer??
    # Duplicated table
    copy = table.copy()
    copy["Inventory"] = np.zeros(copy.shape[0])
    copy["Inventory"].iloc[window] = INIT_AMOUNT
    copy["ShippedQty"] = np.zeros(copy.shape[0])
    copy["ArrivalQty"] = np.zeros(copy.shape[0])
    copy["RefillQty"] = np.zeros(copy.shape[0])
    
    # Initialization
    refill_schedules = []
    on_the_way = 0
    inv = INIT_AMOUNT
    results = list()
    for day in copy.index[window:]:
        # 1. Arrival
        if refill_schedules != []:
            if refill_schedules[0][0]<= day:
                inv += refill_schedules[0][1]
                copy.loc[day,"ArrivalQty"] = refill_schedules[0][1]
                on_the_way -= refill_schedules[0][1]
                refill_schedules.pop(0)

        # 2. Order
        order = copy.loc[ day, "OrderQty"]

        # 3. Ship
        if inv < order:
            copy.loc[day,"ShippedQty"] = inv
            inv = 0
        else:
            copy.loc[ day, "ShippedQty"] = order
            inv -= order

        # 4. Refill
        past_order = copy["OrderQty"][day-timedelta(days = 7*window):day]
        refill = func(LEAD, alpha, past_order, inv, on_the_way)
        if refill > 0 :
            on_the_way += refill
            copy.loc[day,"RefillQty"] = refill
            refill_schedules.append((day+LEAD_WEEK,refill) )
        
        # 5. Inventory - audit
        copy.loc[ day,"Inventory"] = inv
        
    # Report :
    avg = np.mean(table["OrderQty"])
    std = np.std(table["OrderQty"])
    # fulfill = np.mean(copy["ShippedQty"][window:]/copy["OrderQty"][window:])
    rate = sum(copy["ShippedQty"][window:])/sum(copy["OrderQty"][window:])
    maxInv = max(copy["Inventory"][window+LEAD:])
    avgInv = np.mean(copy["Inventory"][window+LEAD:])
    
#     if pr:
#         print("Entering simulator with parameter alpha: %s, window: %d, function: %s "%( alpha, window, func.__name__))
#         print("Average Order Qty: %d, Standard deviation: %.2f"%(avg, std ))
#         print("Fulfillment rate: %.3f" %(rate))
#         #print("Average rate: %.3f" %(rate))
#         print("Maximum Inventory occupation: %d" %maxInv)
#         print("Average Inventory occupation: %.0f"% avgInv)
        
    return avg, std, rate, maxInv, avgInv#, copy["Inventory"]


def parser(x):
    return datetime.strptime(x,"%Y-%m-%d")

if __name__ == '__main__':
    item_list = pd.read_csv('item_miss.csv',header=None)
    item_l = item_list.values.ravel()  #item list 
    a_list = np.arange(0.1, 10.1, 0.1)

for item in item_l[int(ITEM_START):int(ITEM_END)]:
    try:
        data = pd.read_csv("TrainitemByWeek\{}ByWeek.csv".format(item), parse_dates=[0], index_col=0, date_parser=parser)
        
        data["OrderQty"] = [float(x) for x in data["OrderQty"]]
        #alpha = 1.3
        #window = 15
        print('processing item {0}'.format(item))
        item_output = []
        item_output.append(['Fulfillment Rate','Avg Inventory','Max Inventory','Alpha','Window'])
        for alpha in tqdm(a_list):
            for window in range(1, 40):
                Order_QTY, STD, FR, Max_Inv, Avg_Inv = simulator_date(
                    data, alpha, window, ma)
                
                item_output.append([FR, Avg_Inv,Max_Inv,alpha,window])


        with open("output\\MA_%.0f.csv" %item, 'a', newline='') as f:
            spamwriter = csv.writer(f)
            spamwriter.writerows(item_output)
                
    except Exception as e:
        print('load item error: {}'.format(str(e)))
        