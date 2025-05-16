from sqlalchemy import Column , table  , Integer, String  , ForeignKey
from db.database import Base

# inherit model from Base




class User(Base) :

    __tablename__ = "user"
    id = Column(Integer , primary_key=True)
    username = Column(String)
    password = Column(String)
