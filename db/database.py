from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os 
from dotenv import load_dotenv
load_dotenv()

# Defining Database url

DB_URL = os.getenv("PG_DB_URL")

# initilizing engine

engine = create_engine(DB_URL)

# initializing session

Sessions = sessionmaker(autoflush=False , autocommit = False , bind=engine)

# Initializing Base model 

Base = declarative_base()