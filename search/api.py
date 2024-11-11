from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import not_
from sqlalchemy.orm import Session, contains_eager

from booking.models import HotelBooking
from database import get_db
from events.models import Event, Ticket
from hotels.models import Hotel, Room

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def search_results(
    request: Request,
    search_type: str = Query(...),
    city: int = Query(...),
    check_in: str = Query(None),
    check_out: str = Query(None),
    guests: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    results = []

    if search_type == "hotel":
        if (check_in and check_out and guests) and check_in < check_out:
            check_in = datetime.strptime(check_in, "%Y-%m-%d")
            check_out = datetime.strptime(check_out, "%Y-%m-%d")
            available_rooms = (
                db.query(Room)
                .filter(
                    Room.available_from <= check_in,
                    Room.available_until >= check_out,
                    Room.capacity >= guests,
                    not_(
                        db.query(HotelBooking)
                        .filter(
                            HotelBooking.room_id == Room.id,
                            HotelBooking.check_in < check_out,
                            HotelBooking.check_out > check_in,
                            HotelBooking.status.in_(["created", "paid"])
                        )
                        .exists()
                    )
                )
                .subquery()
            )
            results = (
                db.query(Hotel)
                .join(available_rooms, available_rooms.c.hotel_id == Hotel.id)
                .filter(Hotel.city_id == city)
                .options(contains_eager(Hotel.rooms, alias=available_rooms))
                .all()
            )

    elif search_type == "event":
        available_tickets = (
            db.query(Ticket)
            .filter(Ticket.date_start >= datetime.today().date(), Ticket.available_tickets > 0)
            .subquery()
        )
        results = (
            db.query(Event)
            .join(available_tickets, available_tickets.c.event_id == Event.id)
            .filter(Event.city_id == city)
            .options(contains_eager(Event.tickets, alias=available_tickets))
            .all()
        )

    return templates.TemplateResponse(
        "search/search_results.html",
        {"request": request, "results": results, "search_type": search_type},
    )
