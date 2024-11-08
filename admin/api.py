from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.logic import get_current_user
from accounts.models import User
from database import get_db
from models import City, Country

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != "system_admin":
        raise HTTPException(status_code=403, detail="Access forbidden")
    return current_user


@router.get("/countries", response_class=HTMLResponse)
def list_countries(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "admin/countries.html", {"request": request, "countries": countries}
    )


@router.post("/countries/add", response_class=HTMLResponse)
def add_country(
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    new_country = Country(name=name)
    db.add(new_country)
    db.commit()
    return RedirectResponse(url="/admin/countries", status_code=303)


@router.post("/countries/edit/{country_id}", response_class=HTMLResponse)
def edit_country(
    country_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    country.name = name
    db.commit()
    return RedirectResponse(url="/admin/countries", status_code=303)


@router.post("/countries/delete/{country_id}", response_class=HTMLResponse)
def delete_country(
    country_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(country)
    db.commit()
    return RedirectResponse(url="/admin/countries", status_code=303)


@router.get("/cities", response_class=HTMLResponse)
def list_cities(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    cities = db.query(City).all()
    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "admin/cities.html",
        {"request": request, "cities": cities, "countries": countries},
    )


@router.post("/cities/add", response_class=HTMLResponse)
def add_city(
    name: str = Form(...),
    country_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    new_city = City(name=name, country_id=country_id)
    db.add(new_city)
    db.commit()
    return RedirectResponse(url="/admin/cities", status_code=303)


@router.post("/cities/edit/{city_id}", response_class=HTMLResponse)
def edit_city(
    city_id: int,
    name: str = Form(...),
    country_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    city.name = name
    city.country_id = country_id
    db.commit()
    return RedirectResponse(url="/admin/cities", status_code=303)


@router.post("/cities/delete/{city_id}", response_class=HTMLResponse)
def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()
    return RedirectResponse(url="/admin/cities", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    users = db.query(User).all()
    return templates.TemplateResponse(
        "admin/users.html", {"request": request, "users": users}
    )


@router.post("/users/edit/{user_id}", response_class=HTMLResponse)
def edit_user(
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/delete/{user_id}", response_class=HTMLResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
