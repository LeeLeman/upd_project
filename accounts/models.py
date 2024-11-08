from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from common import UserRole
from database import Base


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    patronymic = Column(String)
    contact_number = Column(String)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.USER)

    hotels = relationship("Hotel", back_populates="owner")
    events = relationship("Event", back_populates="owner")
