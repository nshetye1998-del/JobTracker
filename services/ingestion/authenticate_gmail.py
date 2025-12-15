#!/usr/bin/env python3
"""
Gmail OAuth Authentication Script
Run this on your local machine to generate token.pickle
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate():
    """Generate Gmail OAuth token"""
    creds = None
    
    # Check if we already have a token
    if os.path.exists('token.pickle'):
        print('Found existing token.pickle')
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('Refreshing expired token...')
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print('ERROR: credentials.json not found!')
                print('Make sure credentials.json is in the same directory as this script.')
                return
            
            print('Starting OAuth flow...')
            print('Your browser will open for authentication.')
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print('✅ token.pickle created successfully!')
    
    # Test the credentials
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f'\n✅ Successfully authenticated!')
        print(f'   Email: {profile["emailAddress"]}')
        print(f'   Messages: {profile["messagesTotal"]}')
        print(f'\n✅ token.pickle is ready to use with the ingestion service')
    except Exception as e:
        print(f'❌ Error testing credentials: {e}')

if __name__ == '__main__':
    authenticate()
