"""Calendar Schedule mock server."""

import json
from pathlib import Path
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

from env_class import CalendarScheduleSystem

app = FastAPI(title="Calendar Schedule Mock Server")

_seed_path = Path(__file__).parent / "calendar_schedule_task_1.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = CalendarScheduleSystem(init_config=_seed["init_config"])
_env.user_email = _seed["init_config"]["user_email"]
_env.calendars = _seed["init_config"]["calendars"]
_env.events = _seed["init_config"]["events"]
_env.invitations = _seed["init_config"]["invitations"]


@app.get("/get_user_calendars")
def get_user_calendars():
    return _env.get_user_calendars()


@app.get("/get_calendar_by_id")
def get_calendar_by_id(calendar_id: str):
    return _env.get_calendar_by_id(calendar_id=calendar_id)


@app.get("/list_events")
def list_events(calendar_id: str, page: int = 1, page_size: int = 20):
    return _env.list_events(calendar_id=calendar_id, page=page, page_size=page_size)


@app.get("/get_event_by_id")
def get_event_by_id(event_id: str):
    return _env.get_event_by_id(event_id=event_id)


@app.get("/search_events")
def search_events(query: str, calendar_id: str = ""):
    return _env.search_events(query=query, calendar_id=calendar_id)


@app.get("/get_events_by_date_range")
def get_events_by_date_range(start_date: str, end_date: str, calendar_id: str = ""):
    return _env.get_events_by_date_range(start_date=start_date, end_date=end_date, calendar_id=calendar_id)


@app.get("/get_upcoming_events")
def get_upcoming_events(limit: int = 10, calendar_id: str = ""):
    return _env.get_upcoming_events(limit=limit, calendar_id=calendar_id)


@app.get("/get_recurring_event_instances")
def get_recurring_event_instances(event_id: str, start_date: str = "", end_date: str = ""):
    return _env.get_recurring_event_instances(event_id=event_id, start_date=start_date, end_date=end_date)


@app.get("/check_time_slot_availability")
def check_time_slot_availability(start_time: str, end_time: str, user_emails: Optional[List[str]] = Query(None)):
    return _env.check_time_slot_availability(start_time=start_time, end_time=end_time, user_emails=user_emails)


@app.get("/get_meeting_invitations")
def get_meeting_invitations(status: str = ""):
    return _env.get_meeting_invitations(status=status)


@app.get("/get_attendee_status")
def get_attendee_status(event_id: str):
    return _env.get_attendee_status(event_id=event_id)


class CreateEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    calendar_id: str
    location: Optional[str] = ""
    description: Optional[str] = ""
    attendees: Optional[List[str]] = []


@app.post("/create_event")
def create_event(req: CreateEventRequest):
    return _env.create_event(title=req.title, start_time=req.start_time, end_time=req.end_time,
                              calendar_id=req.calendar_id, location=req.location, description=req.description, attendees=req.attendees)


class UpdateEventRequest(BaseModel):
    event_id: str
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


@app.post("/update_event")
def update_event(req: UpdateEventRequest):
    return _env.update_event(event_id=req.event_id, title=req.title, start_time=req.start_time,
                              end_time=req.end_time, location=req.location, description=req.description)


class DeleteEventRequest(BaseModel):
    event_id: str
    delete_all_instances: Optional[bool] = False


@app.post("/delete_event")
def delete_event(req: DeleteEventRequest):
    return _env.delete_event(event_id=req.event_id, delete_all_instances=req.delete_all_instances)


class CreateRecurringEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    calendar_id: str
    recurrence_rule: str
    recurrence_end_date: Optional[str] = ""
    location: Optional[str] = ""


@app.post("/create_recurring_event")
def create_recurring_event(req: CreateRecurringEventRequest):
    return _env.create_recurring_event(title=req.title, start_time=req.start_time, end_time=req.end_time,
                                        calendar_id=req.calendar_id, recurrence_rule=req.recurrence_rule,
                                        recurrence_end_date=req.recurrence_end_date, location=req.location)


class AttendeesRequest(BaseModel):
    event_id: str
    attendee_emails: List[str]


@app.post("/add_attendees_to_event")
def add_attendees_to_event(req: AttendeesRequest):
    return _env.add_attendees_to_event(event_id=req.event_id, attendee_emails=req.attendee_emails)


class RemoveAttendeeRequest(BaseModel):
    event_id: str
    attendee_email: str


@app.post("/remove_attendee_from_event")
def remove_attendee_from_event(req: RemoveAttendeeRequest):
    return _env.remove_attendee_from_event(event_id=req.event_id, attendee_email=req.attendee_email)


class RespondInvitationRequest(BaseModel):
    invitation_id: str
    response: str
    message: Optional[str] = ""


@app.post("/respond_to_invitation")
def respond_to_invitation(req: RespondInvitationRequest):
    return _env.respond_to_invitation(invitation_id=req.invitation_id, response=req.response, message=req.message)


class SetReminderRequest(BaseModel):
    event_id: str
    minutes_before: int
    method: Optional[str] = "notification"


@app.post("/set_event_reminder")
def set_event_reminder(req: SetReminderRequest):
    return _env.set_event_reminder(event_id=req.event_id, minutes_before=req.minutes_before, method=req.method)


class CreateCalendarRequest(BaseModel):
    name: str
    color: Optional[str] = ""
    description: Optional[str] = ""


@app.post("/create_calendar")
def create_calendar(req: CreateCalendarRequest):
    return _env.create_calendar(name=req.name, color=req.color, description=req.description)


class DeleteCalendarRequest(BaseModel):
    calendar_id: str


@app.post("/delete_calendar")
def delete_calendar(req: DeleteCalendarRequest):
    return _env.delete_calendar(calendar_id=req.calendar_id)


class ShareCalendarRequest(BaseModel):
    calendar_id: str
    user_email: str
    permission: str


@app.post("/share_calendar")
def share_calendar(req: ShareCalendarRequest):
    return _env.share_calendar(calendar_id=req.calendar_id, user_email=req.user_email, permission=req.permission)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39203)