from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.api import router as account_router
from admin.api import router as admin_router
from booking.api import router as booking_router
from database import get_db, init_db
from events.api import router as events_router
from hotels.api import router as hotels_router
from middleware import add_user_to_request
from models import City, Country
from schemas import CitySchema
from search.api import router as search_router

app = FastAPI()
init_db()

templates = Jinja2Templates(directory="templates")
app.middleware("http")(add_user_to_request)


app.include_router(account_router, prefix="/accounts")
app.include_router(hotels_router, prefix="/hotels")
app.include_router(events_router, prefix="/events")
app.include_router(search_router, prefix="/search")
app.include_router(booking_router, prefix="/booking")
app.include_router(admin_router, prefix="/admin")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    countries = db.query(Country).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "countries": countries}
    )


@app.get("/cities", response_model=List[CitySchema])
def get_cities_by_country(country_id: int, db: Session = Depends(get_db)):
    cities = db.query(City).filter(City.country_id == country_id).all()
    return cities
