"""
Calendar endpoints.

Provides upcoming birthdays for the authenticated user's contacts,
ordered by next occurrence for the calendar view.
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Contact, User
from app.schemas import BirthdayEventResponse, CalendarData, StandardResponse
from app.core.security import get_current_user
from app.core.constants import FEB29_NON_LEAP_MONTH, FEB29_NON_LEAP_DAY

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _next_birthday_occurrence(birthday: date, today: date) -> tuple[date, int]:
    """
    Compute the next occurrence of a birthday and days until it.

    For Feb 29 in non-leap years, uses March 1 as the occurrence date.

    Args:
        birthday: The contact's birthday (year is ignored).
        today: Reference date (e.g. date.today()).

    Returns:
        Tuple of (next_occurrence, days_until).
    """
    month, day = birthday.month, birthday.day
    if month == 2 and day == 29 and not (today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)):
        month, day = FEB29_NON_LEAP_MONTH, FEB29_NON_LEAP_DAY
    this_year = date(today.year, month, day)
    if this_year >= today:
        next_occurrence = this_year
    else:
        next_year = today.year + 1
        if birthday.month == 2 and birthday.day == 29:
            if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0):
                next_occurrence = date(next_year, 2, 29)
            else:
                next_occurrence = date(next_year, FEB29_NON_LEAP_MONTH, FEB29_NON_LEAP_DAY)
        else:
            next_occurrence = date(next_year, birthday.month, birthday.day)
    days_until = (next_occurrence - today).days
    return next_occurrence, days_until


def get_today() -> date:
    """Return current date. Overridable in tests for deterministic results."""
    return date.today()


@router.get("", response_model=StandardResponse[CalendarData])
async def list_calendar_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    today: date = Depends(get_today),
) -> StandardResponse[CalendarData]:
    """
    List upcoming birthdays for the authenticated user's contacts.

    Only contacts with a birthday set are included. Events are ordered
    by next occurrence (soonest first).
    """
    contacts = db.exec(
        select(Contact).where(
            Contact.user_id == current_user.id,
            Contact.birthday.isnot(None),
        )
    ).all()
    events = []
    for contact in contacts:
        if contact.birthday is None:
            continue
        next_occurrence, days_until = _next_birthday_occurrence(contact.birthday, today)
        events.append(
            BirthdayEventResponse(
                contact_id=str(contact.id),
                contact_name=contact.name,
                birthday=contact.birthday.isoformat(),
                next_occurrence=next_occurrence.isoformat(),
                days_until=days_until,
            )
        )
    events.sort(key=lambda e: e.next_occurrence)
    return StandardResponse[CalendarData](
        status="success",
        data=CalendarData(events=events),
        message="",
    )
