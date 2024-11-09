from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.logic import get_current_user
from accounts.models import User
from common import UserRole
from database import get_db
from hotels.models import Hotel, Room
from models import Country

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_user_hotels(current_user: User, db: Session):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        hotels = db.query(Hotel).all()
    else:
        hotels = db.query(Hotel).filter(Hotel.owner_id == current_user.id).all()
    return hotels


def get_user_hotel(hotel_id: int, current_user: User, db: Session = Depends(get_db)):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    else:
        hotel = (
            db.query(Hotel)
            .filter(Hotel.id == hotel_id, Hotel.owner_id == current_user.id)
            .first()
        )
    return hotel


def get_user_room(room_id: int, current_user: User, db: Session = Depends(get_db)):
    if current_user.role == UserRole.SYSTEM_ADMIN:
        room = db.query(Room).filter(Room.id == room_id).first()
    else:
        room = (
            db.query(Room)
            .join(Hotel, Room.hotel_id == Hotel.id)
            .filter(Room.id == room_id, Hotel.owner_id == current_user.id)
            .first()
        )
    return room


@router.get("/", response_class=HTMLResponse)
def hotels_list_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")
    hotels = get_user_hotels(current_user, db)
    return templates.TemplateResponse(
        "hotels/hotels.html", {"request": request, "hotels": hotels}
    )


@router.get("/add", response_class=HTMLResponse)
def add_hotel_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "hotels/add_hotel.html",
        {"request": request, "countries": countries, "cities": []},
    )


@router.post("/add")
def add_hotel(
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(None),
    stars: int = Form(...),
    city_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    new_hotel = Hotel(
        name=name,
        address=address,
        description=description,
        stars=stars,
        owner_id=current_user.id,
        city_id=city_id,
    )
    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return RedirectResponse("/hotels", status_code=303)


@router.get("/{hotel_id}", response_class=HTMLResponse)
def hotel_detail_page(
    request: Request,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels/", status_code=302)

    return templates.TemplateResponse(
        "hotels/hotel.html", {"request": request, "hotel": hotel}
    )


@router.get("/{hotel_id}/edit", response_class=HTMLResponse)
def edit_hotel_page(
    request: Request,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels", status_code=302)

    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "hotels/edit_hotel.html",
        {"request": request, "hotel": hotel, "countries": countries},
    )


@router.post("/{hotel_id}/edit")
def update_hotel(
    hotel_id: int,
    name: str = Form(...),
    address: str = Form(...),
    description: str = Form(None),
    stars: int = Form(...),
    city_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels", status_code=302)

    hotel.name = name
    hotel.address = address
    hotel.description = description
    hotel.stars = stars
    hotel.city_id = city_id
    db.commit()

    return RedirectResponse(f"/hotels/{hotel_id}", status_code=303)


@router.post("/{hotel_id}/delete")
def delete_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if hotel:
        db.delete(hotel)
        db.commit()
    return RedirectResponse("/hotels", status_code=303)


@router.get("/{hotel_id}/rooms", response_class=HTMLResponse)
def rooms_page(
    request: Request,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels", status_code=302)

    rooms = db.query(Room).filter(Room.hotel_id == hotel_id).all()
    return templates.TemplateResponse(
        "hotels/rooms.html", {"request": request, "hotel": hotel, "rooms": rooms}
    )


@router.get("/{hotel_id}/rooms/add", response_class=HTMLResponse)
def room_page(
    request: Request,
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels", status_code=302)

    return templates.TemplateResponse(
        "hotels/add_room.html", {"request": request, "hotel": hotel}
    )


@router.post("/{hotel_id}/rooms/add")
def add_room(
    hotel_id: int,
    name: str = Form(...),
    capacity: int = Form(...),
    bed_type: str = Form(...),
    bed_number: int = Form(...),
    meal_type: str = Form(...),
    cancellation_policy: str = Form(None),
    price_per_night: float = Form(...),
    available_from: str = Form(...),
    available_until: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    hotel = get_user_hotel(hotel_id, current_user, db)
    if not hotel:
        return RedirectResponse("/hotels", status_code=302)

    new_room = Room(
        name=name,
        capacity=capacity,
        bed_type=bed_type,
        bed_number=bed_number,
        meal_type=meal_type,
        cancellation_policy=cancellation_policy,
        price_per_night=price_per_night,
        available_from=datetime.strptime(available_from, "%Y-%m-%d"),
        available_until=datetime.strptime(available_until, "%Y-%m-%d"),
        hotel_id=hotel_id,
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return RedirectResponse(f"/hotels/{hotel_id}/rooms", status_code=303)


@router.get("/{hotel_id}/rooms/{room_id}", response_class=HTMLResponse)
def room_detail_page(
    request: Request,
    hotel_id: int,
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    room = get_user_room(room_id, current_user, db)
    if not room:
        return RedirectResponse(f"/hotels/{hotel_id}/rooms", status_code=302)

    return templates.TemplateResponse(
        "hotels/room.html", {"request": request, "room": room, "hotel_id": hotel_id}
    )


@router.get("/{hotel_id}/rooms/{room_id}/edit", response_class=HTMLResponse)
def update_room_page(
    request: Request,
    hotel_id: int,
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    room = get_user_room(room_id, current_user, db)
    if not room:
        return RedirectResponse(f"/hotels/{hotel_id}/rooms", status_code=302)

    return templates.TemplateResponse(
        "hotels/edit_room.html",
        {"request": request, "room": room, "hotel_id": hotel_id},
    )


@router.post("/{hotel_id}/rooms/{room_id}/edit")
def update_room(
    hotel_id: int,
    room_id: int,
    name: str = Form(...),
    capacity: int = Form(...),
    bed_type: str = Form(...),
    bed_number: int = Form(...),
    meal_type: str = Form(...),
    cancellation_policy: str = Form(None),
    price_per_night: float = Form(...),
    available_from: str = Form(...),
    available_until: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    room = get_user_room(room_id, current_user, db)
    if not room:
        return RedirectResponse(f"/hotels/{hotel_id}/rooms", status_code=302)

    room.name = name
    room.capacity = capacity
    room.bed_type = bed_type
    room.bed_number = bed_number
    room.meal_type = meal_type
    room.cancellation_policy = cancellation_policy
    room.price_per_night = price_per_night
    room.available_from = datetime.strptime(available_from, "%Y-%m-%d")
    room.available_until = datetime.strptime(available_until, "%Y-%m-%d")
    db.commit()

    return RedirectResponse(f"/hotels/{hotel_id}/rooms/{room_id}", status_code=303)


@router.post("/{hotel_id}/rooms/{room_id}/delete")
def delete_room(
    hotel_id: int,
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    room = get_user_room(room_id, current_user, db)
    if room:
        db.delete(room)
        db.commit()
    return RedirectResponse(f"/hotels/{hotel_id}/rooms", status_code=303)
