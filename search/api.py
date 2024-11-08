from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database import get_db
from events.models import Event
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
        query = db.query(Hotel).filter(Hotel.city_id == city)
        if (check_in and check_out and guests) and check_in < check_out:
            check_in = datetime.strptime(check_in, "%Y-%m-%d")
            check_out = datetime.strptime(check_out, "%Y-%m-%d")
            query = query.filter(
                Hotel.rooms.any(
                    and_(
                        Room.available_from <= check_in,
                        Room.available_until >= check_out,
                    )
                )
            )
            query = query.filter(Hotel.rooms.any(Room.capacity >= guests))
            results = query.all()

    elif search_type == "event":
        results = db.query(Event).filter(Event.city_id == city).all()

    return templates.TemplateResponse(
        "search/search_results.html",
        {"request": request, "results": results, "search_type": search_type},
    )
