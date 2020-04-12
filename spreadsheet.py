# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START sheets_quickstart]
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import sqlite3

LOCAL_DB="offerings_data.db"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_SPREADSHEET_ID = '1JTgJjZcLczxp5DloUkYOpjKmhcSjohtFWWPhLf90gtA'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'
SAMPLE_RANGE_NAME = 'Form Responses 1!A2:Z'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for row in values:
            print(row)
            insert_row(row+[""]*(25-len(row)))

            # Insert into database IF EMAIL NOT IN THERE

def insert_row(row):
    conn=sqlite3.connect(LOCAL_DB)
    cursor=conn.cursor()
    cursor.execute("INSERT or IGNORE into ctmutualaid_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17],row[22],row[24],"False"))
# 0: data
# 1: EMAIL
# 2: case management
# 3: childcard
# 4: cooking
# 5: delivery
# 6: pets
# 7: netflix
# 8: medical
# 9: storage
# 10: Art
# 11: mental health
# 12: Conversation
# 13: cleaning
# 14: legal
# 15: social services
# 16: closed captioning
# 17: additional
# 18: tick-off combo
# 19: concerns
# 20: email(again?)
# 21: location

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
# [END sheets_quickstart]
