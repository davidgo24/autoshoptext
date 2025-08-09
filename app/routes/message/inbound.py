
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, Response
from pydantic import BaseModel
from sqlmodel import Session, select, func, update
from twilio.twiml.messaging_response import MessagingResponse

from app.core.database import get_session
from app.models.contact import Contact
from app.models.incoming_message import IncomingMessage

router = APIRouter()


class InboundMessageSchema(BaseModel):
    from_number: str
    body: str
    created_at: datetime
    contact_name: Optional[str] = None


class InboundMessageResponse(BaseModel):
    messages: List[InboundMessageSchema]


@router.post("/webhooks/twilio/sms", response_class=Response)
async def handle_inbound_sms(
    from_number: str = Form(..., alias="From"),
    to_number: str = Form(..., alias="To"),
    body: str = Form(..., alias="Body"),
    session: Session = Depends(get_session),
):
    """
    Handle incoming SMS messages from Twilio.

    Stores the message and sends a standard auto-reply.
    """
    # Normalize the incoming phone number from E.164 format (e.g., +12223334444) 
    # to the format stored in the database (e.g., 2223334444).
    normalized_from_number = from_number.replace("+1", "", 1)

    result = await session.execute(
        select(Contact).where(Contact.phone_number == normalized_from_number)
    )
    contact = result.scalars().first()

    incoming_message = IncomingMessage(
        from_number=from_number,
        to_number=to_number,
        body=body,
        contact_id=contact.id if contact else None,
    )
    session.add(incoming_message)
    await session.commit()

    twiml_response = MessagingResponse()
    twiml_response.message(
        "Thank you for your message. This inbox is not actively monitored. "
        "Please call the shop directly for assistance (323) 727-28823!"
    )

    return Response(content=str(twiml_response), media_type="application/xml")


from sqlalchemy.orm import selectinload

# ... (rest of the imports)

@router.get("/messages/inbound/unread-count")
async def get_unread_message_count(session: Session = Depends(get_session)):
    """Get the count of unread inbound messages."""
    result = await session.execute(
        select(func.count(IncomingMessage.id)).where(IncomingMessage.is_read == False)
    )
    count = result.scalar_one_or_none() or 0
    return {"unread_count": count}


@router.post("/messages/inbound/mark-as-read")
async def mark_messages_as_read(session: Session = Depends(get_session)):
    """Mark all inbound messages as read."""
    await session.execute(
        update(IncomingMessage).where(IncomingMessage.is_read == False).values(is_read=True)
    )
    await session.commit()
    return {"success": True, "message": "All messages marked as read."}


@router.get("/messages/inbound", response_model=InboundMessageResponse)
async def get_inbound_messages(session: Session = Depends(get_session)):
    """Get all inbound messages, newest first."""
    result = await session.execute(
        select(IncomingMessage)
        .options(selectinload(IncomingMessage.contact))
        .order_by(IncomingMessage.created_at.desc())
    )
    messages = result.scalars().all()

    response_messages = []
    for msg in messages:
        contact_name = None
        if msg.contact:
            contact_name = msg.contact.name
        response_messages.append(InboundMessageSchema(
            from_number=msg.from_number,
            body=msg.body,
            created_at=msg.created_at,
            contact_name=contact_name or "Unknown",
        ))
    return InboundMessageResponse(messages=response_messages)
