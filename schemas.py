from pydantic import BaseModel


class CitySchema(BaseModel):
    id: int
    name: str
    country_id: int

    class Config:
        orm_mode = True
