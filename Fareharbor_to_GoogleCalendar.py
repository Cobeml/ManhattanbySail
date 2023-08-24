#!/usr/bin/env python
# coding: utf-8

#!/usr/bin/env python
# coding: utf-8
"""
Created on Tue Mar 14 16:03:30 2023

@author: cobeliu
@author: amitlowe
"""

from __future__ import print_function
import pandas as pd
import os
import time
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


import hubspot
from hubspot.crm.properties import ApiException
import re
from datetime import datetime
import pytz

from selenium import webdriver
from selenium.webdriver.common.by import By

def is_within_upcoming_week(dt):
    today = datetime.datetime.now().date()
    upcoming_week = today + datetime.timedelta(days=7)
    return today <= dt.date() <= upcoming_week

def is_within_time_range(start_hour, end_hour):
    current_time = datetime.datetime.now(pytz.timezone('EST5EDT')).time()
    start_time = datetime.time(start_hour)
    end_time = datetime.time(end_hour)

    if start_hour < end_hour:
        return start_time <= current_time <= end_time
    else:
        return current_time >= start_time or current_time <= end_time

def download_FH():
    try:
        # Insert the path to the WebDriver executable
        webdriver_path = 'C:\\Path\\To\\chromedriver'
        
        # Insert username and password
        username = 'user'
        password = 'password'
        url = 'https://fareharbor.com/manhattanbysail/login/'
        
        # Initialize the WebDriver
        driver = webdriver.Chrome(executable_path=webdriver_path)
        driver.get(url)
        
        username_xpath = "//input[@name = 'username']"
        password_xpath = "//input[@name = 'password']"
        
        # Find the username and password input fields and enter the credentials
        username_field = driver.find_element(By.XPATH, username_xpath)
        username_field.send_keys(username)
        password_field = driver.find_element(By.XPATH, password_xpath)
        password_field.send_keys(password)
        
        # Click the login button
        login_button = driver.find_element(By.XPATH, "//button[@class = 'btn-big btn-wide btn-blue btn--large-label test-login-button']")
        login_button.click()
        
        # Add a delay to allow the page to load
        time.sleep(5)
        
        # Navigate to the download page and click the download button
        # Replace the URL and the XPath of the download button
        download_page_url = 'https://fareharbor.com/manhattanbysail/dashboard/reports/advanced/payments-and-refunds/?saved=81982'
        generate_button_xpath = "//button[@class = 'btn btn-green']"
        download_button_xpath = "//button[@class = 'tb-btn ']"
        close_button_xpath = "//button[@class = 'overlay-close']"
        
        driver.get(download_page_url)
        time.sleep(5)
        generate_button = driver.find_element(By.XPATH, generate_button_xpath)
        generate_button.click()
        
        time.sleep(15)
        
        close_button = driver.find_element(By.XPATH, close_button_xpath)
        close_button.click()
        
        download_button = driver.find_element(By.XPATH, download_button_xpath)
        download_button.click()
        
        # Close the browser after a delay
        time.sleep(10)
        driver.quit()
    except:
        download_FH()

#Google API Functions
def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    cred = None
    working_dir = os.getcwd()
    token_dir = 'token files'
    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.pickle'

    # check if token dir exists first, if not, create the folder
    if not os.path.exists(os.path.join(working_dir, token_dir)):
        os.mkdir(os.path.join(working_dir, token_dir))
    if os.path.exists(os.path.join(working_dir, token_dir, pickle_file)):
        with open(os.path.join(working_dir, token_dir, pickle_file), 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(os.path.join(working_dir, token_dir, pickle_file), 'wb') as token:
            pickle.dump(cred, token)
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, API_VERSION, 'service created successfully')
        return service
    except Exception as e:
        print(e)
        print(f'Failed to create service instance for {API_SERVICE_NAME}')
        os.remove(os.path.join(working_dir, token_dir, pickle_file))
        return None

CLIENT_SECRET_FILE = "credentials.json"      ################ do not forget to download OAuth json file and put it in current directory!!!!!!!!!!
API_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

service = create_service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

#HubSpot functions
#Unwraps nested dictionary of properties
def unwrap_properties(deals,nested_keys):
    for deal in deals:
        for key in nested_keys:
            deal[key] = deal['properties'][key]
        del deal['properties']
def format_time_12_hours_minutes(string):
    # Check if the string is empty or null
    if not bool(string):
        raise TypeError()  
    elif len(string) < 2:
        raise TypeError()
    #Does not provide functionality for a ranged time
    if '-' in string:
        raise TypeError("Incorrect Formatting. Does not provide functionality for ranged times.")
    
    # Of course if the las two chracters are "ap" or "pa" this gets messed up.
    if ((string[-1].lower() == 'p')  or (string[-2].lower() == 'p')):
        period = 'PM'
    elif ((string[-1].lower() == 'a') or (string[-2].lower() == 'a')):
        period = 'AM'
    else:
        raise TypeError("Incorrect Formatting. No AM/PM given.")
    
    #Removes am/pm signature
    magnitude = re.sub('[apmAPM ]','',string)
    if len(magnitude) == 0:
        raise TypeError("Incorrect Formatting. No magnitude given for the time.")
    colon_pos = magnitude.find(':')
    acceptable_magnitude_chars = ['0','1','2','3','4','5','6','7','8','9',':']
    for char in magnitude:
        if char not in acceptable_magnitude_chars:
            raise TypeError("Incorrect Formatting: " + magnitude)
    
    #If the magnitude has a colon, find the hours, minutes
    if colon_pos != -1:
        minutes = magnitude[colon_pos + 1 : ]
        hours = magnitude[ : colon_pos]
        if len(minutes) > 2:
            print("Minutes formatted incorrectly. Too many digits.")
        if len(hours) > 2:
            print("Hours formatted incorrectly. Too many digits")
        if len(minutes) <  2:
            minutes += '0'
        if len(hours) < 2:
            hours = '0' + hours
    else: #No colon
        if len(magnitude) == 2:
            if int(magnitude) <= 12:
                hours = magnitude
                minutes = '00'
            else:
                raise TypeError(magnitude + "is a improper magnitude for the time.")
        elif len(magnitude) == 1:
            hours = magnitude
            minutes = '00'
        elif len(magnitude) == 3:
            hours = magnitude[0]
            minutes = magnitude[1:]
        elif len(magnitude) == 4:
            hours = magnitude[:2]
            minutes = magnitude[2:]
        else:
            raise TypeError("Cannot have a time with more than 5 digits")
            
    return_string = hours + ':' + minutes + " " + period
    if len(return_string) == 7:
        return_string = '0' + return_string
    return return_string

def empty_or_time(x):
    try:
        return format_time_12_hours_minutes(x)
    except TypeError:
        return ""
    
def concat_datetime(date_and_time):
    if date_and_time[-1] == 'M': # Meaning the time exists
        return datetime.strptime(date_and_time,'%Y-%m-%d+%I:%M %p') #fill the timestrings in
    else:
        return datetime.strptime(date_and_time,'%Y-%m-%d+')



#FH Function
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


def continuously_run_program():
    count = 0;
    while True:
        if count == 0:
            try: 
                download_FH()
                runner(True) # Creates the calendar
            except:
                download_FH()
                runner(True)
        else:
            try: 
                download_FH()
                runner(False) # Creates the calendar
            except:
                download_FH()
                runner(False)
        time.sleep(2*60*60) # Wait for 2 hours
        count += 1
        if count == 12:
            count = 0

def delete_events(calId):
    page_token = None
    while True:
      events = service.events().list(calendarId=calId, pageToken=page_token).execute()
      for event in events['items']:
        print(event)
        service.events().delete(calendarId=calId, eventId=event['id']).execute()
      page_token = events.get('nextPageToken')
      if not page_token:
        break

def FH_upload(file):
    ### reformat csv into dataframe
    source_directory = 'C:\\Users\\Office Admin\\Downloads\\'
    source_file_path = os.path.join(source_directory, file)
    df = pd.read_csv(source_file_path)
    os.remove(source_file_path)

    ### reformat dataframe to ics standards

    df["End Date"] = df["Unnamed: 1"]
    df["Start Time"] = df["Unnamed: 1"]
    df["End Time"] = df["Unnamed: 1"]

    df.rename(columns={"Unnamed: 0":"Subject", "Unnamed: 1":"Start Date", "Sales":"Description"}, inplace=True)
    columns = df.columns
    start_date_index = columns.get_loc('Start Date')
    end_date_index = columns.get_loc('End Date')
    start_time_index = columns.get_loc('Start Time')
    end_time_index = columns.get_loc('End Time')
    description_index = columns.get_loc('Description')
    bookings_index = columns.get_loc('Bookings')
    index = 0
    for string in df["Start Date"]:
        availability_list = string.split()
        if (len(availability_list) > 3):
            date = availability_list[0]
            start_time = availability_list[2]
            end_time = availability_list[4]

            df.iloc[index,start_date_index] = date
            df.iloc[index,end_date_index] = date
            df.iloc[index,start_time_index] = start_time
            df.iloc[index,end_time_index] = end_time

        df.iloc[index,description_index] += " passengers " + df.iloc[index,bookings_index] + " revenue"

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

    df['Start'] = df['Start'].astype(str)
    df['End']   = df['End'].astype(str)

    for i in range(len(df)):
        df.iloc[i,end_index] = df.iloc[i,end_index][:10] + 'T' + df.iloc[i,end_index][11:]
        df.iloc[i,start_index] = df.iloc[i,start_index][:10] + 'T' + df.iloc[i,start_index][11:]
    
    FH_calendar_ids = {
        'crew_FH': '153b753048c375bc5e0e840c2054a67ba43c9a0adaf0654d37de74969e06e8df@group.calendar.google.com',
        'FH': '76f1279dda4cb714614db8cf9b1a3fd0905fbb662c3ff70ac8f51b1cabeb1b1c@group.calendar.google.com',
    }

    #TO DO: Clear FH calendars
    for i in FH_calendar_ids: 
        delete_events(FH_calendar_ids[i])
    
    #Upload FH
    for i in range(len(df)):
        event_row = df.iloc[i]
        start_date_time = event_row['Start']
        start_date_time = start_date_time
        end_date_time = event_row['End']
        end_date_time = end_date_time
        current_time = datetime.now(pytz.timezone('America/New_York'))
        time_str= str(current_time.isoformat())
        event_row['Description'] += '\n\nlast updated: ' + time_str
        description_array = event_row['Description'].split()
        crew_description = description_array[0] + " " + description_array[1]
        colorId = ''
        if 'Shearwater' in event_row['Subject']:
            colorId = '4'
        else:
            colorId = '9'

        FULLEVENT = {
            'summary': event_row['Subject'],
            'colorId': colorId,
            'description': event_row['Description'],
            'start': {'dateTime': start_date_time,
                      'timeZone' : 'US/Eastern'},
            'end': {'dateTime': end_date_time,
                    'timeZone' : 'US/Eastern'},
            }
        
        CREWEVENT = {
            'summary': event_row['Subject'],
            'colorId': colorId,
            'description': crew_description,
            'start': {'dateTime': start_date_time,
                      'timeZone' : 'US/Eastern'},
            'end': {'dateTime': end_date_time,
                    'timeZone' : 'US/Eastern'},
            }
        
        print("start:")
        print(FULLEVENT["start"])
        print("end: ")
        print(FULLEVENT["end"])
        print("name: ")
        print(FULLEVENT["summary"])
        print()
        
        #Upload once to full info calendar and again to public sail crew calendar
        service.events().insert(calendarId=FH_calendar_ids['FH'], body=FULLEVENT).execute()
        service.events().insert(calendarId=FH_calendar_ids['crew_FH'], body=CREWEVENT).execute()

def runner(upload_all):
    file_name = 'Sales--2023-01-01--2023-12-31.csv'
    FH_upload(file_name)
    
    #Here begins the HubSpot part
    client = hubspot.Client.create(access_token="hubspot access token") #insert hubspot access token
    #List to hold all the deals
    deals_fetched = []
    api_response = {}
    desired_properties = ['dealname', 'event_duration__hours_', 'possible_date_for_charter__one_day_', 
                          'deal_stage', 'budget_dropdown', 'number_of_guests', 'dealstage', 'desired_departure_time', 'boat__updated_', "staging_and_production_duration", "breakdown_and_cleanup_duration"]
    length = 100
    after = 0
    while length == 100:
        try:
            api_response = client.crm.deals.basic_api.get_page(limit=100, after = after, properties=desired_properties, archived=False)
        except ApiException as e:
            print("Exception when calling basic_api->get_page: %s\n" % e)

        x = (api_response.to_dict())['results']
        for deal in x:
            deals_fetched.append(deal)
        length = len(x)
        after = x[length - 1]['id']
    property_keys = list((deals_fetched[0]['properties']).keys())
    unwrap_properties(deals_fetched,property_keys)
    deals_frame = pd.DataFrame(deals_fetched)
    unneeded_columns = ['properties_with_history', 'created_at','updated_at', 'archived', 'archived_at', 'associations','createdate','hs_lastmodifieddate','hs_object_id']
    deals_frame.drop(columns=unneeded_columns, inplace=True)
    #Rename columns
    deals_frame.rename(columns={"desired_departure_time":"Stated Start Time", "dealname":"Subject", "possible_date_for_charter__one_day_":"Start Date","event_duration__hours_":"Duration"},inplace=True)
    #Drop rows where the start date is not specified
    deals_frame = deals_frame.dropna(axis=0, subset=['Start Date'])
    deals_frame['stated duration'] = deals_frame['Duration']
    deals_frame['Duration'] = deals_frame['Duration'].astype(float).abs()
    deals_frame['Duration'].fillna(0.5,inplace=True)
    deals_frame['Staging Duration'] = deals_frame['staging_and_production_duration'].astype(float).abs()
    deals_frame['Staging Duration'].fillna(0.5,inplace=True)
    deals_frame['Staging Duration'] = pd.to_timedelta(deals_frame['Staging Duration'],unit='hours')
    deals_frame['Breakdown Duration'] = deals_frame['Duration'].astype(float).abs()
    deals_frame['Breakdown Duration'].fillna(0.5,inplace=True)
    deals_frame['Breakdown Duration'] = pd.to_timedelta(deals_frame['Breakdown Duration'],unit='hours')
    deals_frame['stated start time'] = deals_frame['Stated Start Time']
    deals_frame['Start Time'] = deals_frame['Stated Start Time']
    #Removes values such as 'afternoon' or ranged values, replaces them with empty Strings
    deals_frame['Start Time'] = deals_frame['Start Time'].apply(lambda x : empty_or_time(x)) - deals_frame['Staging Duration']
    deals_frame['Start'] = deals_frame['Start Date'] + '+' + deals_frame['Start Time']
    deals_frame['Start'] = deals_frame['Start'].apply(lambda x: concat_datetime(x)) - deals_frame['Staging Duration']
    deals_frame['Duration'] = pd.to_timedelta(deals_frame['Duration'],unit='hours')
    deals_frame['End'] = deals_frame['Start'] + deals_frame['Duration'] + deals_frame['Staging Duration'] + deals_frame['Breakdown Duration']


    deals_frame['Description'] = ""
    columns = deals_frame.columns
    description_index = columns.get_loc('Description')
    stage_index = columns.get_loc('dealstage')
    budget_index = columns.get_loc('budget_dropdown')
    guests_index = columns.get_loc('number_of_guests')
    stated_start_index = columns.get_loc('Stated Start Time')
    stated_departure_time_index = columns.get_loc('stated departure time')
    stated_duration_index = columns.get_loc('stated duration')
    staging_duration_index = columns.get_loc('staging_and_production_duration')
    breakdown_duration_index = columns.get_loc('breakdown_and_cleanup_duration')
		

    
    for i in range(len(deals_frame)):
        
        a2 = deals_frame.iloc[i,budget_index]
        if a2 is None:
            a2 = "No Budget Given"
        a3 = deals_frame.iloc[i,guests_index]
        if a3 is None:
            a3 = "No Guest Number Given"
        a4 = deals_frame.iloc[i,stated_start_index]
        if a4 is None:
            a4 = "No Start Given"
        a5 = deals_frame.iloc[i,stated_duration_index]
        if a5 is None:
            a5 = "No Duration Given"
        a6 = deals_frame.iloc[i,stated_departure_time_index]
        if a6 is None:
            a6 = "No Time Given"
        a7 = deals_frame.iloc[i,staging_duration_index]
        if a7 is None:
            a7 = "No Staging Necessary"
            a8 = deals_frame.iloc[i,breakdown_duration_index]
        if a8 is None:
            a8 = "No Breakdown Necessary"
        
        deals_frame.iloc[i,description_index] = 'Budget: ' + a2 + ' | Guests: ' + a3 + ' | Stated Start: ' + a4 + ' | Sail Duration (Hours): ' + a5 + ' | Departure Time: ' + a6 + ' | Staging Duration (Hours): ' + a7 + ' | Breakdown Duration (Hours): ' + a8   
        
    gcalendar = deals_frame[['Subject','Start Date','Start','End','Description']]
    deals_frame['Start'] = deals_frame['Start'].astype(str)
    deals_frame['End']   = deals_frame['End'].astype(str)
    end_index = deals_frame.columns.get_loc('End')
    start_index = deals_frame.columns.get_loc('Start')

    for i in range(len(deals_frame)):
        deals_frame.iloc[i,end_index] = deals_frame.iloc[i,end_index][:10] + 'T' + deals_frame.iloc[i,end_index][11:]
        deals_frame.iloc[i,start_index] = deals_frame.iloc[i,start_index][:10] + 'T' + deals_frame.iloc[i,start_index][11:]
    
    calendar_ids = {
        'crew_HS': '36983933fadf51b4362f36ee1dc4ccc1c2ba4762076bc269133c8b63a5f2bce2@group.calendar.google.com',
        'closed_event_completed': '992a6c946f0b839f4d56273f8755e9a1809e85867da8d97b099af628bd3fe79b@group.calendar.google.com',
        'closed_lost': '035801937f286b59414bd5571a88c56f9219800545edcfb916b3eac20b067162@group.calendar.google.com',
        'deposit_received_contract_signed': '255f81a91c7f6bce8a1739c1fbd82748a4ec57fa3a576b83c440a94fb1457315@group.calendar.google.com',
        'initial_lead': '3b8f43f6a806c8a5cfe10dcd7e73b8e2e40cf4acc089a00e9e0685e2728909c3@group.calendar.google.com',
        'paid_in_full': '40e9f1a8cc37c2d6af284d7a42a873b6354b591efae6a6df5889fa3634d85f29@group.calendar.google.com',
        'serious_discussions_quoted': 'c612e54878fa2dc9e28a570651050f623d64c5f184d71e6943776e247a511711@group.calendar.google.com',
        'verbal_confirmation': '71846a8d778984eb74d537af982fe4c7381a2734f20b6ca232062f4c1c63d1cf@group.calendar.google.com',
        'warm_leads': 'd664393b89dc4905ca9d81b41319aca0e3c458d2cd47cd576024f9256875eaa1@group.calendar.google.com',
				'cancelled_for_reschedule': '70fc2c96980fce97dacf8de2d10039ad5ffb1a8c977dc046225ca305a5b504b5@group.calendar.google.com',
    }

    #TO DO: Clear all calendars
    for i in calendar_ids: 
        isImportant = i != 'initial_lead' and i != 'warm_leads' and i != 'closed_lost'
        if isImportant or upload_all:
            delete_events(calendar_ids[i])
    
    #Upload HS
    for i in range(len(deals_frame.index)):        
        event_row = deals_frame.iloc[i]
        start_date_time = event_row['Start']
        start_date_time = start_date_time
        end_date_time = event_row['End']
        end_date_time = end_date_time
        current_time = datetime.now(pytz.timezone('America/New_York'))
        time_str= str(current_time.isoformat())
        event_row['Description'] += '\n\nlast updated: ' + time_str
        description_array = event_row['Description'].split()
        afterGuests = False
        crew_description = ''
        for word in description_array:
            if word == 'Guests:':
                afterGuests = True
            if afterGuests:
                crew_description += word + ' '

        colorId = ''
        summary = ''
        if event_row['boat__updated_'] == 'Shearwater':
            colorId = '5'
            summary = event_row['Subject'] + ' - Shearwater'
        else:
            colorId = '7'
            summary = event_row['Subject'] + ' - Clipper City'

        FULLEVENT = {
            'summary': summary,
            'colorId': colorId,
            'description': event_row['Description'],
            'start': {'dateTime': start_date_time,
                      'timeZone' : 'US/Eastern'},
            'end': {'dateTime': end_date_time,
                    'timeZone' : 'US/Eastern'},
            }

        CREWEVENT = {
            'summary': summary,
            'colorId': colorId,
            'description': crew_description,
            'start': {'dateTime': start_date_time,
                      'timeZone' : 'US/Eastern'},
            'end': {'dateTime': end_date_time,
                    'timeZone' : 'US/Eastern'},
            }
        print("start:")
        print(FULLEVENT["start"])
        print("end: ")
        print(FULLEVENT["end"])
        print("name: ")
        print(FULLEVENT["summary"])
        print()
        #Upload events to their respective calendar based on deal stage
        deal_stage = deals_frame.iloc[i,stage_index]
        if deal_stage == 'closedwon':
            service.events().insert(calendarId=calendar_ids['closed_event_completed'], body=FULLEVENT).execute()
            service.events().insert(calendarId=calendar_ids['crew_HS'], body=CREWEVENT).execute()
        elif deal_stage == 'closedlost' and upload_all:
            service.events().insert(calendarId=calendar_ids['closed_lost'], body=FULLEVENT).execute()
        elif deal_stage == '17951058':
            service.events().insert(calendarId=calendar_ids['deposit_received_contract_signed'], body=FULLEVENT).execute()
            service.events().insert(calendarId=calendar_ids['crew_HS'], body=CREWEVENT).execute()
        elif deal_stage == 'appointmentscheduled' and upload_all:
            service.events().insert(calendarId=calendar_ids['initial_lead'], body=FULLEVENT).execute()
        elif deal_stage == '18022060':
            service.events().insert(calendarId=calendar_ids['paid_in_full'], body=FULLEVENT).execute()
            service.events().insert(calendarId=calendar_ids['crew_HS'], body=CREWEVENT).execute()
        elif deal_stage == 'presentationscheduled':
            service.events().insert(calendarId=calendar_ids['serious_discussions_quoted'], body=FULLEVENT).execute()
        elif deal_stage == 'decisionmakerboughtin':
            service.events().insert(calendarId=calendar_ids['verbal_confirmation'], body=FULLEVENT).execute()
        elif deal_stage == 'qualifiedtobuy' and upload_all:
            service.events().insert(calendarId=calendar_ids['warm_leads'], body=FULLEVENT).execute()
        elif deal_stage == '72139337' and upload_all:
            service.events().insert(calendarId=calendar_ids['cancelled_for_reschedule'], body=FULLEVENT).execute()
        #Upload booked events once to full info calendar and then again to charter crew calendar


continuously_run_program()
