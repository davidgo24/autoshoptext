
import asyncio
import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# It's important that all models are imported here so SQLModel knows about them
from app.models.vin import VIN
from app.models.service_record import ServiceRecord
from app.models.contact import Contact
from app.models.vin_contact_link import VINContactLink
from app.models.scheduled_message import ScheduledMessage
from app.models.incoming_message import IncomingMessage

async def create_db_and_tables():
    """
    One-time script to create all database tables based on the SQLModel metadata.
    """
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set.")
        return

    print(f"Connecting to database...")
    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        print("Dropping all existing tables (if they exist)...")
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Tables created successfully.")

    await engine.dispose()

if __name__ == "__main__":
    print("Running database table creation script...")
    asyncio.run(create_db_and_tables())
