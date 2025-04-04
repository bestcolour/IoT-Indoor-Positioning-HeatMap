from sqlalchemy import create_engine,Engine,text
from dotenv import load_dotenv
load_dotenv()  # take environment variables
import os

class MySQL_Connection():
    # Replace with your credentials
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    PORT_NUM = os.getenv("PORT_NUM")
    HOST = os.getenv("HOST")

    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{HOST}:{PORT_NUM}/{DB_NAME}"

    # Create an engine
    engine :Engine = create_engine(DATABASE_URL)

    # Test connection
    with engine.connect() as conn :
        result = conn.execute(text("SELECT DATABASE();"))
        print(result.fetchone())  # Should print your database name


mysql_database = MySQL_Connection()