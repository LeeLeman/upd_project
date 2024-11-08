from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


class Hotel(Base):
    __tablename__ = "hotel"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    description = Column(String)
    stars = Column(Integer, nullable=False, default=0)

    owner_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    owner = relationship("User", back_populates="hotels")

    city_id = Column(Integer, ForeignKey("city.id", ondelete="SET NULL"))
    city = relationship("City", back_populates="hotels")

    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "room"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    bed_type = Column(String)
    bed_number = Column(Integer, nullable=False, default=0)
    meal_type = Column(String)
    cancellation_policy = Column(String)
    price_per_night = Column(Float, nullable=False, default=0)
    available_from = Column(DateTime)
    available_until = Column(DateTime)

    hotel_id = Column(Integer, ForeignKey("hotel.id", ondelete="CASCADE"))
    hotel = relationship("Hotel", back_populates="rooms")

    bookings = relationship("HotelBooking", back_populates="room")
