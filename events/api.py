from datetime import date, time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.logic import get_current_user
from accounts.models import User
from common import UserRole
from database import get_db
from events.models import Event, Ticket
from models import Country

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_user_events(current_user: User, db: Session):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        events = db.query(Event).all()
    else:
        events = db.query(Event).filter(Event.owner_id == current_user.id).all()
    return events


def get_user_event(event_id: int, current_user: User, db: Session = Depends(get_db)):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        event = db.query(Event).filter(Event.id == event_id).first()
    else:
        event = (
            db.query(Event)
            .filter(Event.id == event_id, Event.owner_id == current_user.id)
            .first()
        )
    return event


def get_user_ticket(ticket_id: int, current_user: User, db: Session = Depends(get_db)):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    else:
        ticket = (
            db.query(Ticket)
            .join(Event, Ticket.event_id == Event.id)
            .filter(Ticket.id == ticket_id, Event.owner_id == current_user.id)
            .first()
        )
    return ticket


@router.get("/", response_class=HTMLResponse)
def events_list_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    events = get_user_events(current_user, db)
    return templates.TemplateResponse(
        "events/events.html", {"request": request, "events": events}
    )


@router.get("/add", response_class=HTMLResponse)
def add_event_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "events/add_event.html",
        {"request": request, "countries": countries, "cities": []},
    )


@router.post("/add")
def add_event(
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(None),
    age_limit: int = Form(...),
    city_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    new_event = Event(
        name=name,
        address=address,
        description=description,
        age_limit=age_limit,
        owner_id=current_user.id,
        city_id=city_id,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return RedirectResponse("/events", status_code=303)


@router.get("/{event_id}", response_class=HTMLResponse)
def event_detail_page(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)
    return templates.TemplateResponse(
        "events/event.html", {"request": request, "event": event}
    )


@router.get("/{event_id}/edit", response_class=HTMLResponse)
def edit_event_page(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)

    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "events/edit_event.html",
        {"request": request, "event": event, "countries": countries},
    )


@router.post("/{event_id}/edit")
def update_event(
    event_id: int,
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(None),
    age_limit: int = Form(...),
    city_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)

    event.name = name
    event.address = address
    event.description = description
    event.age_limit = age_limit
    event.city_id = city_id
    db.commit()

    return RedirectResponse(f"/events/{event_id}", status_code=303)


@router.post("/{event_id}/delete")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if event:
        db.delete(event)
        db.commit()
    return RedirectResponse("/events", status_code=303)


@router.get("/{event_id}/tickets", response_class=HTMLResponse)
def tickets_page(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)

    tickets = db.query(Ticket).filter(Ticket.event_id == event_id).all()
    return templates.TemplateResponse(
        "events/tickets.html", {"request": request, "event": event, "tickets": tickets}
    )


@router.get("/{event_id}/tickets/add", response_class=HTMLResponse)
def room_page(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)

    return templates.TemplateResponse(
        "events/add_ticket.html", {"request": request, "event": event}
    )


@router.post("/{event_id}/tickets/add")
def add_ticket(
    event_id: int,
    name: str = Form(...),
    date_start: date = Form(...),
    time_start: time = Form(None),
    available_tickets: int = Form(...),
    cancellation_policy: str = Form(None),
    price: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    event = get_user_event(event_id, current_user, db)
    if not event:
        return RedirectResponse("/events/", status_code=302)

    new_ticket = Ticket(
        name=name,
        date_start=date_start,
        time_start=time_start,
        available_tickets=available_tickets,
        cancellation_policy=cancellation_policy,
        price=price,
        event_id=event_id,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return RedirectResponse(f"/events/{event_id}/tickets", status_code=303)


@router.get("/{event_id}/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail_page(
    request: Request,
    event_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    ticket = get_user_ticket(ticket_id, current_user, db)
    if not ticket:
        return RedirectResponse(f"/events/{event_id}/tickets", status_code=302)

    return templates.TemplateResponse(
        "events/ticket.html",
        {"request": request, "ticket": ticket, "event_id": event_id},
    )


@router.get("/{event_id}/tickets/{ticket_id}/edit", response_class=HTMLResponse)
def update_ticket_page(
    request: Request,
    event_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    ticket = get_user_ticket(ticket_id, current_user, db)
    if not ticket:
        return RedirectResponse(f"/events/{event_id}/tickets", status_code=302)

    return templates.TemplateResponse(
        "events/edit_ticket.html",
        {"request": request, "ticket": ticket, "event_id": event_id},
    )


@router.post("/{event_id}/tickets/{ticket_id}/edit")
def update_ticket(
    request: Request,
    event_id: int,
    ticket_id: int,
    name: str = Form(...),
    date_start: date = Form(...),
    time_start: time = Form(None),
    available_tickets: int = Form(...),
    cancellation_policy: str = Form(None),
    price: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    ticket = get_user_ticket(ticket_id, current_user, db)
    if not ticket:
        return RedirectResponse(f"/events/{event_id}/tickets", status_code=302)

    ticket.name = name
    ticket.date_start = date_start
    ticket.time_start = time_start
    ticket.available_tickets = available_tickets
    ticket.cancellation_policy = cancellation_policy
    ticket.price = price
    db.commit()

    return RedirectResponse(f"/events/{event_id}/tickets/{ticket_id}", status_code=303)


@router.post("/{event_id}/tickets/{ticket_id}/delete")
def delete_ticket(
    event_id: int,
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    ticket = get_user_ticket(ticket_id, current_user, db)
    if ticket:
        db.delete(ticket)
        db.commit()
    return RedirectResponse(f"/events/{event_id}/tickets", status_code=303)
