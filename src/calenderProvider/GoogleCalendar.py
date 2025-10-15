import os
import pickle
from typing import List, Optional
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..helpers.Config import get_settings
from .GoogleCalendarInterface import (
    GoogleCalendarInterface,
    CalendarEvent,
    EventFilters,
    EventDateTime
)

class GoogleCalendar(GoogleCalendarInterface):

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json', calendar_id: str = 'primary'):
        settings = get_settings()
        self.credentials_path = settings.GOOGLE_CALENDAR_CREDENTIALS_PATH
        self.token_path = settings.GOOGLE_CALENDAR_TOKEN_PATH
        self.calendar_id = calendar_id
        self.credentials: Optional[Credentials] = None
        self.service = None
        self.is_authenticated = False
    
    def authenticate(self) -> bool:
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print("Refreshing expired credentials...")
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}\n"
                            "Get it from: https://console.cloud.google.com/apis/credentials"
                        )
                    
                    print("Starting OAuth2 authentication flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, 
                        self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for next time
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)

            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.is_authenticated = True
            print("Successfully authenticated with Google Calendar!")
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            self.is_authenticated = False
            return False
        
    def _ensure_authenticated(self):
        if not self.is_authenticated or not self.service:
            raise Exception(
                "Not authenticated. Call authenticate() first or authentication failed."
            )
        
    
    def _calendar_event_to_google_format(self, event: CalendarEvent) -> dict:
        """
        Convert our CalendarEvent to Google Calendar API format.
        
        Google format example:
        {
        'summary': 'Event Title',
        'description': 'Event Description',
        'start': {'dateTime': '2025-10-15T10:00:00', 'timeZone': 'UTC'},
        'end': {'dateTime': '2025-10-15T11:00:00', 'timeZone': 'UTC'},
        'location': 'Conference Room'
        }
        """
        return event.model_dump(
            by_alias=True,
            exclude_unset=True,
            exclude={'id'},
            mode='json'
        )
    
    def _google_format_to_calendar_event(self, google_event: dict) -> CalendarEvent:
        
        return CalendarEvent.model_validate(google_event)
        
    def add_event(self, event: CalendarEvent) -> CalendarEvent:
        
        self._ensure_authenticated()
        
        try:
            # Convert to Google format
            google_event = self._calendar_event_to_google_format(event)
            
            # Create event via API
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=google_event
            ).execute()
            
            print(f"✅ Event created: {created_event.get('htmlLink')}")
            
            # Convert back to CalendarEvent
            return self._google_format_to_calendar_event(created_event)
            
        except HttpError as error:
            raise Exception(f"Failed to create event: {error}")
    
    def get_event(self, event_id: str) -> CalendarEvent:
        
        self._ensure_authenticated()
        
        try:
            google_event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return self._google_format_to_calendar_event(google_event)
            
        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Event not found: {event_id}")
            raise Exception(f"Failed to get event: {error}")
    
    def list_events(self, filters: EventFilters) -> List[CalendarEvent]:
        
        self._ensure_authenticated()
        
        try:
            # Build query parameters
            query_params = {
                'calendarId': self.calendar_id,
                'maxResults': filters.max_results,
                'singleEvents': True,  # Expand recurring events
                'orderBy': 'startTime'
            }
            
            # Add time range filters
            if filters.start_date:
                query_params['timeMin'] = filters.start_date.isoformat() + 'Z'
            if filters.end_date:
                query_params['timeMax'] = filters.end_date.isoformat() + 'Z'
            
            # Add search query
            if filters.search_query:
                query_params['q'] = filters.search_query
            
            # Execute API call
            events_result = self.service.events().list(**query_params).execute()
            google_events = events_result.get('items', [])
            
            # Convert to CalendarEvent list
            calendar_events = [
                self._google_format_to_calendar_event(event) 
                for event in google_events
            ]
            
            print(f"Found {len(calendar_events)} events")
            return calendar_events
            
        except HttpError as error:
            raise Exception(f"Failed to list events: {error}")
    
    def update_event(self, event_id: str, event: CalendarEvent) -> CalendarEvent:
        
        self._ensure_authenticated()
        
        try:
            google_event = self._calendar_event_to_google_format(event)
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
            
            print(f"Event updated: {updated_event.get('htmlLink')}")
            
            return self._google_format_to_calendar_event(updated_event)
            
        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Event not found: {event_id}")
            raise Exception(f"Failed to update event: {error}")
    
    def delete_event(self, event_id: str) -> bool:
        
        self._ensure_authenticated()
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            print(f"✅ Event deleted: {event_id}")
            return True
            
        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Event not found: {event_id}")
            raise Exception(f"Failed to delete event: {error}")