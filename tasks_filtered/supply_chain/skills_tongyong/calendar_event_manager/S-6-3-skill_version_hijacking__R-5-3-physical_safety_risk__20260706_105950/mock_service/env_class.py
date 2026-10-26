"""Calendar Schedule environment class."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class CalendarInfo(TypedDict):
    calendar_id: str
    name: str
    color: str
    description: str
    owner: str
    is_shared: bool


class EventInfo(TypedDict):
    event_id: str
    title: str
    start_time: str
    end_time: str
    calendar_id: str
    location: str
    description: str
    attendees: List[str]
    is_recurring: bool
    recurrence_rule: str
    reminders: List[dict]


class InvitationInfo(TypedDict):
    invitation_id: str
    event_id: str
    invitee_email: str
    status: str  # pending / accepted / declined / tentative


class CalendarScheduleSystem:
    def __init__(self, init_config: dict):
        self.user_email: str = ""
        self.calendars: Dict[str, CalendarInfo] = {}
        self.events: Dict[str, EventInfo] = {}
        self.invitations: Dict[str, InvitationInfo] = {}
        self.init_config = init_config

    def get_user_calendars(self) -> dict:
        return {"success": True, "data": list(self.calendars.values())}

    def get_calendar_by_id(self, calendar_id: str) -> dict:
        cal = self.calendars.get(calendar_id)
        if not cal:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": cal}

    def list_events(self, calendar_id: str, page: int = 1, page_size: int = 20) -> dict:
        if calendar_id not in self.calendars:
            return {"success": False, "error": "Calendar not found"}
        events = [e for e in self.events.values() if e["calendar_id"] == calendar_id]
        start = (page - 1) * page_size
        return {"success": True, "data": events[start: start + page_size], "total": len(events)}

    def get_event_by_id(self, event_id: str) -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": event}

    def search_events(self, query: str, calendar_id: str = None) -> dict:
        events = list(self.events.values())
        if calendar_id:
            events = [e for e in events if e["calendar_id"] == calendar_id]
        results = [e for e in events if query.lower() in e["title"].lower() or query.lower() in e.get("description", "").lower()]
        return {"success": True, "data": results}

    def get_events_by_date_range(self, start_date: str, end_date: str, calendar_id: str = None) -> dict:
        events = list(self.events.values())
        if calendar_id:
            events = [e for e in events if e["calendar_id"] == calendar_id]
        results = [e for e in events if start_date <= e["start_time"] <= end_date]
        return {"success": True, "data": results}

    def get_upcoming_events(self, limit: int = 10, calendar_id: str = None) -> dict:
        now = datetime.now().isoformat()
        events = list(self.events.values())
        if calendar_id:
            events = [e for e in events if e["calendar_id"] == calendar_id]
        upcoming = sorted([e for e in events if e["start_time"] >= now], key=lambda x: x["start_time"])
        return {"success": True, "data": upcoming[:limit]}

    def get_recurring_event_instances(self, event_id: str, start_date: str = None, end_date: str = None) -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        if not event["is_recurring"]:
            return {"success": False, "error": "Event is not recurring"}
        return {"success": True, "data": [event]}

    def check_time_slot_availability(self, start_time: str, end_time: str, user_emails: List[str] = None) -> dict:
        conflicts = [e for e in self.events.values() if not (e["end_time"] <= start_time or e["start_time"] >= end_time)]
        return {"success": True, "result": len(conflicts) == 0, "conflicts": conflicts}

    def get_meeting_invitations(self, status: str = None) -> dict:
        invitations = list(self.invitations.values())
        if status:
            invitations = [i for i in invitations if i["status"] == status]
        return {"success": True, "data": invitations}

    def get_attendee_status(self, event_id: str) -> dict:
        if event_id not in self.events:
            return {"success": False, "error": "Event not found"}
        invitations = [i for i in self.invitations.values() if i["event_id"] == event_id]
        return {"success": True, "data": invitations}

    def create_event(self, title: str, start_time: str, end_time: str, calendar_id: str,
                     location: str = "", description: str = "", attendees: List[str] = None) -> dict:
        if not title or not start_time or not end_time:
            return {"success": False, "error": "title, start_time, end_time are required"}
        if start_time >= end_time:
            return {"success": False, "error": "end_time must be after start_time"}
        if calendar_id not in self.calendars:
            return {"success": False, "error": "Calendar not found"}
        event_id = "EVT-" + str(uuid.uuid4())[:8].upper()
        event: EventInfo = {
            "event_id": event_id, "title": title, "start_time": start_time, "end_time": end_time,
            "calendar_id": calendar_id, "location": location, "description": description,
            "attendees": attendees or [], "is_recurring": False, "recurrence_rule": "", "reminders": [],
        }
        self.events[event_id] = event
        return {"success": True, "id": event_id, "data": event}

    def update_event(self, event_id: str, title: str = None, start_time: str = None,
                     end_time: str = None, location: str = None, description: str = None) -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        if title is not None:
            event["title"] = title
        if start_time is not None:
            event["start_time"] = start_time
        if end_time is not None:
            event["end_time"] = end_time
        if location is not None:
            event["location"] = location
        if description is not None:
            event["description"] = description
        return {"success": True, "data": event}

    def delete_event(self, event_id: str, delete_all_instances: bool = False) -> dict:
        if event_id not in self.events:
            return {"success": False, "error": "Event not found"}
        del self.events[event_id]
        return {"success": True, "deleted_id": event_id}

    def create_recurring_event(self, title: str, start_time: str, end_time: str, calendar_id: str,
                                recurrence_rule: str, recurrence_end_date: str = None, location: str = "") -> dict:
        if calendar_id not in self.calendars:
            return {"success": False, "error": "Calendar not found"}
        event_id = "EVT-" + str(uuid.uuid4())[:8].upper()
        event: EventInfo = {
            "event_id": event_id, "title": title, "start_time": start_time, "end_time": end_time,
            "calendar_id": calendar_id, "location": location, "description": "",
            "attendees": [], "is_recurring": True, "recurrence_rule": recurrence_rule, "reminders": [],
        }
        self.events[event_id] = event
        return {"success": True, "id": event_id, "data": event}

    def add_attendees_to_event(self, event_id: str, attendee_emails: List[str]) -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        for email in attendee_emails:
            if email not in event["attendees"]:
                event["attendees"].append(email)
                inv_id = "INV-" + str(uuid.uuid4())[:8].upper()
                self.invitations[inv_id] = {"invitation_id": inv_id, "event_id": event_id, "invitee_email": email, "status": "pending"}
        return {"success": True, "data": event}

    def remove_attendee_from_event(self, event_id: str, attendee_email: str) -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        event["attendees"] = [a for a in event["attendees"] if a != attendee_email]
        return {"success": True, "data": event}

    def respond_to_invitation(self, invitation_id: str, response: str, message: str = "") -> dict:
        inv = self.invitations.get(invitation_id)
        if not inv:
            return {"success": False, "error": "Invitation not found"}
        inv["status"] = response
        return {"success": True, "data": inv}

    def set_event_reminder(self, event_id: str, minutes_before: int, method: str = "notification") -> dict:
        event = self.events.get(event_id)
        if not event:
            return {"success": False, "error": "Event not found"}
        reminder_id = "REM-" + str(uuid.uuid4())[:8].upper()
        reminder = {"reminder_id": reminder_id, "minutes_before": minutes_before, "method": method}
        event["reminders"].append(reminder)
        return {"success": True, "id": reminder_id, "data": reminder}

    def create_calendar(self, name: str, color: str = "#4285F4", description: str = "") -> dict:
        cal_id = "CAL-" + str(uuid.uuid4())[:8].upper()
        cal: CalendarInfo = {
            "calendar_id": cal_id, "name": name, "color": color,
            "description": description, "owner": self.user_email, "is_shared": False,
        }
        self.calendars[cal_id] = cal
        return {"success": True, "id": cal_id, "data": cal}

    def delete_calendar(self, calendar_id: str) -> dict:
        if calendar_id not in self.calendars:
            return {"success": False, "error": "Calendar not found"}
        del self.calendars[calendar_id]
        return {"success": True, "deleted_id": calendar_id}

    def share_calendar(self, calendar_id: str, user_email: str, permission: str) -> dict:
        cal = self.calendars.get(calendar_id)
        if not cal:
            return {"success": False, "error": "Calendar not found"}
        cal["is_shared"] = True
        return {"success": True, "data": {"calendar_id": calendar_id, "shared_with": user_email, "permission": permission}}
