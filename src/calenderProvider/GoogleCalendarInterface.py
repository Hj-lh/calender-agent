from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventDateTime(BaseModel):
    date_time: datetime = Field(..., alias='dateTime')
    time_zone: str = Field(default="UTC", alias='timeZone')

    model_config = ConfigDict(populate_by_name=True)
    @field_validator('time_zone')
    @classmethod
    def validate_timezone(cls, v):
        """Ensures timezone is not empty"""
        if not v or v.strip() == "":
            raise ValueError("Timezone cannot be empty")
        return v
    
class CalendarEvent(BaseModel):
    """Represents a calendar event with all its details"""
    id: Optional[str] = None  
    title: str = Field(..., min_length=1, max_length=200, alias='summary')  # Google uses 'summary'
    description: Optional[str] = Field(None, max_length=1000)
    start_time: EventDateTime = Field(..., alias='start')
    end_time: EventDateTime = Field(..., alias='end')
    location: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class EventFilters(BaseModel):
    """Filters for searching/listing events"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_query: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=100)


class GoogleCalendarInterface(ABC):

    
    @abstractmethod
    def authenticate(self) -> bool:

        pass
    
    @abstractmethod
    def add_event(self, event: CalendarEvent) -> CalendarEvent:

        pass
    
    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent:

        pass
    
    @abstractmethod
    def list_events(self, filters: EventFilters) -> List[CalendarEvent]:

        pass
    
    @abstractmethod
    def update_event(self, event_id: str, event: CalendarEvent) -> CalendarEvent:

        pass
    
    @abstractmethod
    def delete_event(self, event_id: str) -> bool:

        pass