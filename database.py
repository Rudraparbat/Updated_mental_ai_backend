from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Defining Database url

DB_URL = "sqlite:///./user.db"

# initilizing engine

engine = create_engine(DB_URL , connect_args={"check_same_thread" : False})

# initializing session

Sessions = sessionmaker(autoflush=False , autocommit = False , bind=engine)

# Initializing Base model 

Base = declarative_base()