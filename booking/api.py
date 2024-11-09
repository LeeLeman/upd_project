from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.logic import get_current_user
from accounts.models import User
from booking.models import EventBooking, HotelBooking
from common import LOGIN_PAGE, PaymentStatus, UserRole
from database import get_db
from events.models import Event, Ticket
from hotels.models import Hotel, Room

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_user_bookings(current_user: User, db: Session):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        hotel_bookings = db.query(HotelBooking).all()
        event_bookings = db.query(EventBooking).all()
    elif current_user.role == UserRole.EXTRANET_ADMIN:
        hotel_bookings = (
            db.query(HotelBooking)
            .join(Room, HotelBooking.room_id == Room.id)
            .join(Hotel, Room.hotel_id == Hotel.id)
            .filter(Hotel.owner_id == current_user.id)
            .all()
        )
        event_bookings = (
            db.query(EventBooking)
            .join(Ticket, EventBooking.ticket_id == Ticket.id)
            .join(Event, Ticket.event_id == Event.id)
            .filter(Event.owner_id == current_user.id)
            .all()
        )
    else:
        hotel_bookings = (
            db.query(HotelBooking).filter(HotelBooking.user_id == current_user.id).all()
        )
        event_bookings = (
            db.query(EventBooking).filter(EventBooking.user_id == current_user.id).all()
        )
    return hotel_bookings, event_bookings


def get_user_room_booking(booking_id: int, current_user: User, db: Session):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        booking = db.query(HotelBooking).filter(HotelBooking.id == booking_id).first()
    elif current_user.role == UserRole.EXTRANET_ADMIN:
        booking = (
            db.query(HotelBooking)
            .join(Room, HotelBooking.room_id == Room.id)
            .join(Hotel, Room.hotel_id == Hotel.id)
            .filter(HotelBooking.id == booking_id, Hotel.owner_id == current_user.id)
            .first()
        )
    else:
        booking = (
            db.query(HotelBooking)
            .filter(
                HotelBooking.id == booking_id, HotelBooking.user_id == current_user.id
            )
            .first()
        )
    return booking


def get_user_ticket_booking(booking_id: int, current_user: User, db: Session):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        booking = db.query(EventBooking).filter(EventBooking.id == booking_id).first()
    elif current_user.role == UserRole.EXTRANET_ADMIN:
        booking = (
            db.query(EventBooking)
            .join(Ticket, EventBooking.ticket_id == Ticket.id)
            .join(Event, Ticket.event_id == Event.id)
            .filter(EventBooking.id == booking_id, Event.owner_id == current_user.id)
            .first()
        )
    else:
        booking = (
            db.query(EventBooking)
            .filter(
                EventBooking.id == booking_id, EventBooking.user_id == current_user.id
            )
            .first()
        )
    return booking


@router.get("/")
def bookings_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(LOGIN_PAGE)

    hotel_bookings, event_bookings = get_user_bookings(current_user, db)
    return templates.TemplateResponse(
        "booking/bookings.html",
        {
            "request": request,
            "hotel_bookings": hotel_bookings,
            "event_bookings": event_bookings,
        },
    )


@router.get("/room_booking/{booking_id}")
def room_booking_details(
    request: Request,
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_room_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    nights = (booking.check_out - booking.check_in).days
    price = booking.room.price_per_night * nights

    return templates.TemplateResponse(
        "booking/room_booking.html",
        {"request": request, "booking": booking, "price": price},
    )


@router.get("/ticket_booking/{booking_id}")
def ticket_booking_details(
    request: Request,
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_ticket_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    price = booking.ticket.price * booking.tickets

    return templates.TemplateResponse(
        "booking/event_booking.html",
        {"request": request, "booking": booking, "price": price},
    )


@router.get("/room/{room_id}", response_class=HTMLResponse)
def room_booking_form(
    request: Request,
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return templates.TemplateResponse(
        "booking/room_booking_form.html",
        {
            "request": request,
            "room": room,
        },
    )


@router.post("/room/{room_id}", response_class=HTMLResponse)
async def book_room(
    room_id: int,
    request: Request,
    check_in: str = Form(...),
    check_out: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    form_data = await request.form()
    guests = []
    guest_count = 1
    while f"guest_first_name_{guest_count}" in form_data:
        guest = {
            "first_name": form_data[f"guest_first_name_{guest_count}"],
            "last_name": form_data[f"guest_last_name_{guest_count}"],
            "patronymic": form_data.get(f"guest_patronymic_{guest_count}", ""),
        }
        guests.append(guest)
        guest_count += 1

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    booking = HotelBooking(
        check_in=datetime.strptime(check_in, "%Y-%m-%d"),
        check_out=datetime.strptime(check_out, "%Y-%m-%d"),
        guest_list=guests,
        room_id=room_id,
        user_id=current_user.id,
    )
    db.add(booking)
    db.commit()

    return templates.TemplateResponse(
        "booking/confirmation.html",
        {"request": request, "booking_id": booking.id, "booking_object": "room"},
    )


@router.post("/ticket/{ticket_id}")
def book_ticket(
    request: Request,
    ticket_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if quantity > ticket.available_tickets:
        raise HTTPException(status_code=400, detail="Not enough tickets available")

    booking = EventBooking(
        tickets=quantity,
        ticket_id=ticket_id,
        user_id=request.state.user.get("user_id"),
    )
    db.add(booking)
    db.commit()

    return templates.TemplateResponse(
        "booking/confirmation.html",
        {"request": request, "booking_id": booking.id, "booking_object": "ticket"},
    )


@router.post("/room_booking/{booking_id}/pay")
def pay_room_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_room_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.PAID
    db.commit()

    return RedirectResponse(url=f"/booking/room_booking/{booking_id}", status_code=303)


@router.post("/room_booking/{booking_id}/cancel")
def cancel_room_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_room_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.CANCELLED
    db.commit()

    return RedirectResponse(url="/booking", status_code=303)


@router.post("/ticket_booking/{booking_id}/pay")
def pay_ticket_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_ticket_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.PAID
    db.commit()

    return RedirectResponse(url=f"/booking/ticket_booking/{booking_id}", status_code=303)


@router.post("/ticket_booking/{booking_id}/cancel")
def cancel_ticket_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_ticket_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.CANCELLED
    db.commit()

    return RedirectResponse(url="/booking", status_code=303)


@router.post("/room_booking/{booking_id}/complete")
def complete_room_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_room_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.COMPLETED
    db.commit()

    return RedirectResponse(url=f"/booking/room_booking/{booking_id}", status_code=303)


@router.post("/ticket_booking/{booking_id}/complete")
def complete_ticket_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    booking = get_user_ticket_booking(booking_id, current_user, db)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = PaymentStatus.COMPLETED
    db.commit()

    return RedirectResponse(url=f"/booking/ticket_booking/{booking_id}", status_code=303)
