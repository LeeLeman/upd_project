from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from accounts.logic import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from accounts.models import User
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("accounts/login.html", {"request": request})


@router.post("/login")
def login_user(
    email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="user", value=access_token)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("user")
    return response


@router.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request):
    return templates.TemplateResponse("accounts/register.html", {"request": request})


@router.post("/register")
def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    patronymic: str = Form(None),
    contact_number: str = Form(None),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(password)
    new_user = User(
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
        contact_number=contact_number,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return templates.TemplateResponse(
        "accounts/confirmation.html", {"request": request}
    )


@router.get("/manage", response_class=HTMLResponse)
def manage_account(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/accounts/login")
    return templates.TemplateResponse(
        "accounts/manage.html", {"request": request, "user": current_user}
    )


@router.post("/manage", response_class=HTMLResponse)
def update_account(
    first_name: str = Form(...),
    last_name: str = Form(...),
    patronymic: str = Form(None),
    contact_number: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/accounts/login")

    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.patronymic = patronymic
    current_user.contact_number = contact_number
    db.commit()
    return RedirectResponse(url="/accounts/manage", status_code=303)
