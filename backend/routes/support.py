from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from database.connection import get_db
from models.domain import User, SupportTicket, TicketMessage, AdminNotification
from auth.security import get_current_user
from schemas.support import SupportTicketCreate, SupportTicketResponse, TicketMessageCreate, TicketMessageResponse, SupportTicketDetailResponse

router = APIRouter(prefix="/api/support/tickets", tags=["Support"])

@router.post("", response_model=SupportTicketResponse)
def create_ticket(ticket_in: SupportTicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    new_ticket = SupportTicket(
        ticket_number=ticket_number,
        customer_id=current_user.id,
        subject=ticket_in.subject,
        description=ticket_in.description,
        category=ticket_in.category,
        priority=ticket_in.priority
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Notify Admin
    notif = AdminNotification(
        title="New Support Ticket",
        message=f"Ticket {ticket_number} created by {current_user.full_name}",
        type="SUPPORT",
        link=f"/admin/support/{new_ticket.id}"
    )
    db.add(notif)
    db.commit()
    
    return new_ticket

@router.get("", response_model=List[SupportTicketResponse])
def get_user_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == current_user.id).all()
    return tickets

@router.get("/{ticket_id}", response_model=SupportTicketDetailResponse)
def get_user_ticket_details(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id, SupportTicket.customer_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    return ticket

@router.post("/{ticket_id}/reply", response_model=TicketMessageResponse)
def reply_to_ticket(ticket_id: int, msg_in: TicketMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id, SupportTicket.customer_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    new_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type="CUSTOMER",
        message=msg_in.message,
        attachment_url=msg_in.attachment_url,
        is_internal=False
    )
    db.add(new_msg)
    
    # If ticket was waiting for customer, change back to in progress
    if ticket.status == "WAITING_FOR_CUSTOMER":
        ticket.status = "IN_PROGRESS"
    
    ticket.updated_at = datetime.utcnow()
    
    # Notify Admin
    notif = AdminNotification(
        title="New Ticket Reply",
        message=f"Customer replied to ticket {ticket.ticket_number}",
        type="SUPPORT",
        link=f"/admin/support/{ticket.id}"
    )
    db.add(notif)
    
    db.commit()
    db.refresh(new_msg)
    return new_msg
