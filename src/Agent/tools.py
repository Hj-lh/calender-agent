from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..calenderProvider.GoogleCalendar import GoogleCalendar
from ..calenderProvider.GoogleCalendarInterface import CalendarEvent, EventDateTime, EventFilters

def get_calendar_tools(calendar_provider: Optional[GoogleCalendar] = None):
    if calendar_provider is None:
        calendar_provider = GoogleCalendar()
        if not calendar_provider.is_authenticated:
            calendar_provider.authenticate()
    calendar = calendar_provider

    class AddEventInput(BaseModel):
        """Schema for adding a calendar event"""
        title: str = Field(..., description="Event title/summary")
        start_datetime: str = Field(..., description="Start datetime in ISO format: YYYY-MM-DDTHH:MM:SS (e.g., 2025-10-18T14:00:00)")
        end_datetime: str = Field(..., description="End datetime in ISO format: YYYY-MM-DDTHH:MM:SS (e.g., 2025-10-18T15:00:00)")
        description: Optional[str] = Field(None, description="Event description/notes")
        location: Optional[str] = Field(None, description="Event location/address")
        timezone: str = Field(default="UTC", description="Timezone (e.g., 'America/New_York', 'UTC')")
    
    
    class ListEventsInput(BaseModel):
        """Schema for listing calendar events"""
        start_date: Optional[str] = Field(None, description="Filter by start date (ISO format: YYYY-MM-DDTHH:MM:SS)")
        end_date: Optional[str] = Field(None, description="Filter by end date (ISO format: YYYY-MM-DDTHH:MM:SS)")
        search_query: Optional[str] = Field(None, description="Search term to filter events by title/description")
        max_results: int = Field(default=10, description="Maximum number of events to return (1-100)")
    
    
    class GetEventInput(BaseModel):
        """Schema for getting a specific event"""
        event_id: str = Field(..., description="Unique event ID")
    
    
    class UpdateEventInput(BaseModel):
        """Schema for updating an event"""
        event_id: str = Field(..., description="Event ID to update")
        title: Optional[str] = Field(None, description="New event title")
        start_datetime: Optional[str] = Field(None, description="New start datetime (ISO format)")
        end_datetime: Optional[str] = Field(None, description="New end datetime (ISO format)")
        description: Optional[str] = Field(None, description="New description")
        location: Optional[str] = Field(None, description="New location")
        timezone: str = Field(default="UTC", description="Timezone")
    
    
    class DeleteEventInput(BaseModel):
        """Schema for deleting an event"""
        event_id: str = Field(..., description="Event ID to delete")

    @tool(args_schema=AddEventInput)
    def add_calendar_event(
        title: str,
        start_datetime: str,
        end_datetime: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "UTC"
    ) -> str:
        
        try:
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = datetime.fromisoformat(end_datetime)
            event = CalendarEvent(
                title=title,
                description=description,
                start_time=EventDateTime(date_time=start_dt, time_zone=timezone),
                end_time=EventDateTime(date_time=end_dt, time_zone=timezone),
                location=location
            )

            created = calendar.add_event(event)
            return f"Event added with ID: {created.title} ({created.id})"
        except Exception as e:
            return f"Failed to add event: {str(e)}"
        
    @tool(args_schema=ListEventsInput)
    def list_calendar_events(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search_query: Optional[str] = None,
        max_results: int = 10
    ) -> str:
        
        try:
            filters = EventFilters(
                start_date=datetime.fromisoformat(start_date) if start_date else None,
                end_date=datetime.fromisoformat(end_date) if end_date else None,
                search_query=search_query,
                max_results=max_results
            )
            
            events = calendar.list_events(filters)
            
            if not events:
                return "📅 No events found matching your criteria."
            
            response = f"📅 Found {len(events)} event(s):\n\n"
            for i, event in enumerate(events, 1):
                response += f"{i}. **{event.title}**\n"
                response += f"   🕒 {event.start_time.date_time.strftime('%A, %B %d at %I:%M %p')} - {event.end_time.date_time.strftime('%I:%M %p')}\n"
                if event.location:
                    response += f"   📍 {event.location}\n"
                if event.description:
                    response += f"   📝 {event.description[:100]}{'...' if len(event.description) > 100 else ''}\n"
                response += f"   🆔 ID: {event.id}\n\n"
            
            return response
        except Exception as e:
            return f"❌ Failed to list events: {str(e)}"
        
    @tool(args_schema=GetEventInput)
    def get_calendar_event(event_id: str) -> str:
        
        try:
            event = calendar.get_event(event_id)
            response = f"📅 **{event.title}**\n"
            response += f"🕒 Start: {event.start_time.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            response += f"🕒 End: {event.end_time.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            if event.location:
                response += f"📍 Location: {event.location}\n"
            if event.description:
                response += f"📝 Description: {event.description}\n"
            response += f"🆔 ID: {event.id}"
            return response
        except Exception as e:
            return f"❌ Failed to get event: {str(e)}"
    
    
    @tool(args_schema=UpdateEventInput)
    def update_calendar_event(
        event_id: str,
        title: Optional[str] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "UTC"
    ) -> str:
        
        try:
            event = calendar.get_event(event_id)
            
            if title: 
                event.title = title
            if description is not None: 
                event.description = description
            if location is not None: 
                event.location = location
            if start_datetime:
                event.start_time.date_time = datetime.fromisoformat(start_datetime)
                event.start_time.time_zone = timezone
            if end_datetime:
                event.end_time.date_time = datetime.fromisoformat(end_datetime)
                event.end_time.time_zone = timezone
            
            updated = calendar.update_event(event_id, event)
            return f"✅ Successfully updated '{updated.title}'!"
        except Exception as e:
            return f"❌ Failed to update event: {str(e)}"
        

    @tool(args_schema=DeleteEventInput)
    def delete_calendar_event(event_id: str) -> str:
        """
        Delete a calendar event permanently.
        Use this when the user wants to remove or cancel an event.
        IMPORTANT: Always confirm with the user before deleting!
        """
        try:
            calendar.delete_event(event_id)
            return f"✅ Event successfully deleted from calendar!"
        except Exception as e:
            return f"❌ Failed to delete event: {str(e)}"
        
    return [
        add_calendar_event,
        list_calendar_events,
        get_calendar_event,
        update_calendar_event,
        delete_calendar_event
    ]