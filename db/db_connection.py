from sqlalchemy import create_engine,Engine,text
from dotenv import load_dotenv
load_dotenv()  # take environment variables
import os

class MySQL_Connection():
    # Replace with your credentials
    def __init__(self):
        # Initialize with environment variables
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.PORT_NUM = os.getenv("PORT_NUM")
        self.HOST = os.getenv("HOST")

        # Construct the database URL
        self.DATABASE_URL = f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.HOST}:{self.PORT_NUM}/{self.DB_NAME}"

        # Create engine
        self.engine: Engine = create_engine(self.DATABASE_URL)

    def test_connection(self):
        try:
            # Test the connection by executing a simple query
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT DATABASE();"))
                print(f"Connected to database: {result.fetchone()[0]}")
        except Exception as e:
            print(f"Error occurred while connecting to the database: {e}")
        

    def clear_table(self,table_names:list):
        try:
            # Test the connection by executing a simple query
            with self.engine.connect() as conn:
                for table in table_names:
                    conn.execute(text(f"DELETE FROM {table}"))
                    conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name=f{table}"))
                # conn.commit() # unnecessary
        except Exception as e:
            print(f"Error occurred while connecting to the database: {e}")



connection = MySQL_Connection()
connection.test_connection()