from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from common import PaymentStatus
from database import Base


class HotelBooking(Base):
    __tablename__ = "hotelbooking"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    guest_list = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default=PaymentStatus.CREATED)

    room_id = Column(Integer, ForeignKey("room.id", ondelete="SET NULL"))
    room = relationship("Room", back_populates="bookings")

    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    user = relationship("User")


class EventBooking(Base):
    __tablename__ = "eventbooking"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    tickets = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default=PaymentStatus.CREATED)

    ticket_id = Column(Integer, ForeignKey("ticket.id", ondelete="SET NULL"))
    ticket = relationship("Ticket", back_populates="bookings")

    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    user = relationship("User")
