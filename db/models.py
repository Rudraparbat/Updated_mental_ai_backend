from pydantic import EmailStr
from sqlalchemy import Column , table  , Integer, String  , ForeignKey 
from db.database import Base

# inherit model from Base


class MentalUser(Base) :

    __tablename__ = "Mentaluser"
    id = Column(Integer , primary_key=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    set_password = Column(String)
