from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class SupportTicketBase(BaseModel):
    subject: str
    description: str
    category: str = "GENERAL_INQUIRY"
    priority: str = "NORMAL"
    device_id: Optional[int] = None
    farm_id: Optional[int] = None
    order_id: Optional[str] = None

class SupportTicketCreate(SupportTicketBase):
    pass

class TicketAttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_size: int
    mime_type: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TicketMessageBase(BaseModel):
    message: str
    attachment_url: Optional[str] = None

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketInternalNoteCreate(BaseModel):
    note: str

class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    sender_type: str
    message: str
    attachment_url: Optional[str] = None
    is_internal: bool
    created_at: datetime
    attachments: List[TicketAttachmentResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class TicketInternalNoteResponse(BaseModel):
    id: int
    ticket_id: int
    admin_id: int
    note: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SupportTicketResponse(BaseModel):
    id: int
    ticket_number: Optional[str] = None
    customer_id: int
    farmer_id: Optional[int] = None
    device_id: Optional[int] = None
    farm_id: Optional[int] = None
    order_id: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    subject: str
    description: str
    category: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SupportTicketSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    closed_tickets: int

class PaginatedTicketsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    tickets: List[SupportTicketResponse]

class SupportTicketDetailResponse(SupportTicketResponse):
    messages: List[TicketMessageResponse] = []
    internal_notes: List[TicketInternalNoteResponse] = []
    
    # Extended customer info
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
