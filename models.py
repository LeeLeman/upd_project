from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Country(Base):
    __tablename__ = "country"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)

    cities = relationship("City", back_populates="country")


class City(Base):
    __tablename__ = "city"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)

    country_id = Column(Integer, ForeignKey("country.id", ondelete="CASCADE"))
    country = relationship("Country", back_populates="cities")

    hotels = relationship("Hotel", back_populates="city")
    events = relationship("Event", back_populates="city")
