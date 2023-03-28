#!/usr/bin/env python
# coding: utf-8

# In[3]:


"""
Created on Tue Mar 14 16:03:30 2023

@author: cobeliu
@author: amitlowe
"""
from __future__ import print_function
import pandas as pd
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import argparse


### reformat csv into dataframe

df = pd.read_csv("FHCalendar.csv")

### reformat dataframe to ics standards

df["End Date"] = df["Unnamed: 1"]
df["Start Time"] = df["Unnamed: 1"]
df["End Time"] = df["Unnamed: 1"]

df.rename(columns={"Unnamed: 0":"Subject", "Unnamed: 1":"Start Date", "Sales":"Description"}, inplace=True)
index = 0
for string in df["Start Date"]:
    availability_list = string.split()
    if (len(availability_list) > 3):
        date = availability_list[0]
        start_time = availability_list[2]
        end_time = availability_list[4]
        
        df["Start Date"][index] = date
        df["End Date"][index] = date
        df["Start Time"][index] = start_time
        df["End Time"][index] = end_time
        
    df["Description"][index] += " passengers " + df["Bookings"][index] + " revenue"
    
    index += 1

df.drop(df.index[0], inplace=True)
df.drop(df.index[len(df) - 1], inplace=True)
df.drop(columns=["Bookings","Unnamed: 4"], inplace=True)
        

df["All Day"] = False
df["Location"] = "NYC"
df["UID"] = 501

df = df[df["Subject"] != "Gift Card"]
df = df.reset_index()
df.drop(columns=["index"], inplace=True)


from datetime import datetime

def format_time(time_string):
    if not ":" in time_string:
        time_list = list(time_string)
        time_list.pop()
        period = time_list.pop()
        time_string = ""
        for j in time_list:
            time_string += j
        time_string = time_string + ":00 " + period.upper() + "M"
    else:
        period = time_string[-2]
        if (time_string[1] == ":"):
            time_string = time_string[0] + ":" + time_string[2:4] + " " + period.upper() + "M"
        else:
            time_string = time_string[0:2] + ":" + time_string[3:5] + " " + period.upper() + "M"
    #if len(time_string) < 7:
    #    time_string = "0" + time_string
    return time_string
    

df['Start'] = df['Start Date'] + "+" + df['Start Time']
df['End'] = df['End Date'] + "+" + df['End Time']
columns = df.columns
start_time_index = columns.get_loc('Start Time')
end_time_index = columns.get_loc('End Time')
start_date_index = columns.get_loc('Start Date')
start_index = columns.get_loc('Start')
end_index = columns.get_loc('End')



date_str = '%m/%d/%y'
hour_str = '%I:%M %p'
for i in range(df.shape[0]):
    df.iloc[i,start_time_index] = format_time(df.iloc[i,start_time_index])
    df.iloc[i,end_time_index] = format_time(df.iloc[i,end_time_index])


df['Start'] = df['Start Date'] + "+" + df['Start Time']
df['End'] = df['End Date'] + "+" + df['End Time']
columns = df.columns
start_time_index = columns.get_loc('Start Time')
end_time_index = columns.get_loc('End Time')
start_date_index = columns.get_loc('Start Date')
start_index = columns.get_loc('Start')
end_index = columns.get_loc('End')



time_str = '%m/%d/%y+%I:%M %p'
for i in range(df.shape[0]):    
    df.iloc[i,end_index] = datetime.strptime(df.iloc[i,end_index],time_str)
    df.iloc[i,start_index] = datetime.strptime(df.iloc[i,start_index],time_str)


try:
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
   
SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json',SCOPES)
    creds = tools.run_flow(flow,store,flags) \
            if flags else tools.run(flow, store)
CAL = build('calendar', 'v3', http=creds.authorize(Http()))

def CSV_to_Google(event_row):
    start_date_time = (str(event_row['Start'])).replace(" ","T")
    start_date_time = start_date_time + "-05:00"
    end_date_time = (str(event_row['End'])).replace(" ","T")
    end_date_time = end_date_time + "-05:00"
    EVENT = {
        'summary': event_row['Subject'],
        'description': event_row['Description'],
        'start': {'dateTime': start_date_time},
        'end': {'dateTime': end_date_time},
    }
    
    CAL.events().insert(calendarId='c4a91dddf2c0e811c1c34cd9bacb3310ac93b97c8a548d4905e22dcba51c3146@group.calendar.google.com',
                        sendNotifications=True, body=EVENT).execute()

events_result = CAL.events().list(calendarId='c4a91dddf2c0e811c1c34cd9bacb3310ac93b97c8a548d4905e22dcba51c3146@group.calendar.google.com').execute()
events = events_result.get('items', [])

for event in events:
    CAL.events().delete(calendarId='c4a91dddf2c0e811c1c34cd9bacb3310ac93b97c8a548d4905e22dcba51c3146@group.calendar.google.com', eventId=event['id']).execute()

for i in range(df.shape[0]):
    CSV_to_Google(df.iloc[i])

# save name and date into 

