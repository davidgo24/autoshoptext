import os
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models.vin import VIN
from app.models.service_record import ServiceRecord
from app.models.contact import Contact
from app.models.vin_contact_link import VINContactLink
from app.models.scheduled_message import ScheduledMessage
from sqlalchemy import text

# Load env vars from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # Best-effort: add service_record_id to scheduledmessage if it doesn't exist
        try:
            await conn.execute(text("ALTER TABLE scheduledmessage ADD COLUMN service_record_id INTEGER"))
        except Exception:
            # Column may already exist or dialect may differ; ignore
            pass
        try:
            # Ensure index can exist in some DBs; ignore failures
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_scheduledmessage_service_record_id ON scheduledmessage(service_record_id)"))
        except Exception:
            pass
        # Add is_reminder column (Postgres-safe) and backfill
        try:
            await conn.execute(text("ALTER TABLE IF EXISTS scheduledmessage ADD COLUMN IF NOT EXISTS is_reminder BOOLEAN DEFAULT FALSE"))
        except Exception:
            pass
        try:
            await conn.execute(text("UPDATE scheduledmessage SET is_reminder = TRUE WHERE is_reminder = FALSE AND LOWER(message_content) LIKE '%reminder%'"))
        except Exception:
            pass
        # Add created_at column
        try:
            await conn.execute(text("ALTER TABLE IF EXISTS scheduledmessage ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()"))
        except Exception:
            pass
