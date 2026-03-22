import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self.authenticate()
    
    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('calendar', 'v3', credentials=creds)
    
    def obtener_eventos_hoy(self):
        hoy = datetime.now()
        hoy_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        hoy_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        eventos = self.service.events().list(
            calendarId='primary',
            timeMin=hoy_inicio.isoformat() + '-03:00',
            timeMax=hoy_fin.isoformat() + '-03:00',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return eventos.get('items', [])
