from pydantic import BaseModel

class SendMessageRequest(BaseModel):
    service_record_id: int
    contact_id: int
    immediate_message_content: str
