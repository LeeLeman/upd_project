from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from database import Base


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    description = Column(String)
    age_limit = Column(Integer)

    owner_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    owner = relationship("User", back_populates="events")

    city_id = Column(Integer, ForeignKey("city.id", ondelete="SET NULL"))
    city = relationship("City", back_populates="events")

    tickets = relationship(
        "Ticket", back_populates="event", cascade="all, delete-orphan"
    )


class Ticket(Base):
    __tablename__ = "ticket"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    date_start = Column(Date, nullable=False)
    time_start = Column(Time)
    available_tickets = Column(Integer, nullable=False, default=0)
    cancellation_policy = Column(String)
    price = Column(Float, nullable=False, default=0)

    event_id = Column(Integer, ForeignKey("event.id", ondelete="CASCADE"))
    event = relationship("Event", back_populates="tickets")

    bookings = relationship("EventBooking", back_populates="ticket")
