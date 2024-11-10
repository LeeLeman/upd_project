from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from common import UserRole

DATABASE_URL = "sqlite:///./sqlite.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_admin_user(db: Session):
    from accounts.logic import hash_password
    from accounts.models import User

    admin_exists = db.query(User).filter(User.role == UserRole.SYSTEM_ADMIN).first()
    if not admin_exists:
        admin_user = User(
            first_name="Admin",
            last_name="Admin",
            email="admin@test.ru",
            contact_number="+71234567899",
            password=hash_password("admin123"),
            role=UserRole.SYSTEM_ADMIN,
        )
        db.add(admin_user)
        db.commit()


def init_db():
    import accounts.models
    import booking.models
    import events.models
    import hotels.models
    import models

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        create_admin_user(session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
