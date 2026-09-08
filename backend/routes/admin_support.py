from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.domain import User, SupportTicket, TicketMessage, TicketInternalNote, AdminNotification
from auth.security import get_current_user
from schemas.support import (
    SupportTicketResponse, SupportTicketDetailResponse, 
    TicketMessageCreate, TicketMessageResponse,
    TicketInternalNoteCreate, TicketInternalNoteResponse
)

router = APIRouter(prefix="/api/admin/support/tickets", tags=["Admin Support"])

def check_admin(user: User):
    if user.role not in ['super_admin', 'admin', 'support_agent']:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.get("", response_model=dict)
def get_all_tickets(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    assigned_to: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    query = db.query(SupportTicket, User.full_name, User.phone_number)\
              .join(User, SupportTicket.customer_id == User.id)
              
    if status:
        query = query.filter(SupportTicket.status == status)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if category:
        query = query.filter(SupportTicket.category == category)
    if assigned_to:
        query = query.filter(SupportTicket.assigned_agent_id == assigned_to)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(or_(
            SupportTicket.ticket_number.ilike(search_filter),
            SupportTicket.subject.ilike(search_filter),
            User.full_name.ilike(search_filter),
            User.phone_number.ilike(search_filter)
        ))
        
    total = query.count()
    results = query.order_by(desc(SupportTicket.updated_at)).offset(skip).limit(limit).all()
    
    formatted_results = []
    for ticket, customer_name, customer_phone in results:
        ticket_dict = {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "customer_id": ticket.customer_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "assigned_agent_id": ticket.assigned_agent_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "closed_at": ticket.closed_at
        }
        formatted_results.append(ticket_dict)
        
    return {
        "total": total,
        "items": formatted_results
    }

@router.get("/stats")
def get_support_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    
    total = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "OPEN").count()
    in_progress = db.query(SupportTicket).filter(SupportTicket.status == "IN_PROGRESS").count()
    resolved = db.query(SupportTicket).filter(SupportTicket.status == "RESOLVED").count()
    high_priority = db.query(SupportTicket).filter(SupportTicket.priority.in_(["HIGH", "CRITICAL"])).count()
    created_today = db.query(SupportTicket).filter(SupportTicket.created_at >= start_of_today).count()
    
    return {
        "total": total,
        "open": open_tickets,
        "in_progress": in_progress,
        "resolved": resolved,
        "high_priority": high_priority,
        "created_today": created_today
    }

@router.get("/{ticket_id}", response_model=SupportTicketDetailResponse)
def get_ticket_details(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    customer = db.query(User).filter(User.id == ticket.customer_id).first()
    
    response_data = {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "customer_id": ticket.customer_id,
        "customer_name": customer.full_name if customer else None,
        "customer_email": customer.email if customer else None,
        "customer_phone": customer.phone_number if customer else None,
        "assigned_agent_id": ticket.assigned_agent_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "closed_at": ticket.closed_at,
        "messages": ticket.messages,
        "internal_notes": ticket.internal_notes
    }
    return response_data

@router.put("/{ticket_id}/assign")
def assign_ticket(ticket_id: int, agent_id: int = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.assigned_agent_id = agent_id
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Assigned successfully"}

@router.put("/{ticket_id}/status")
def update_status(ticket_id: int, status: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.status = status
    if status in ['RESOLVED', 'CLOSED']:
        if not ticket.closed_at:
            ticket.closed_at = datetime.utcnow()
    else:
        ticket.closed_at = None
        
    ticket.updated_at = datetime.utcnow()
    
    # Notify Customer (Stub - Would send email or push to a user notification table)
    # print(f"Notify User {ticket.customer_id}: Ticket {ticket.ticket_number} status changed to {status}")
    db.commit()
    return {"message": "Status updated successfully"}

@router.put("/{ticket_id}/priority")
def update_priority(ticket_id: int, priority: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.priority = priority
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Priority updated successfully"}

@router.post("/{ticket_id}/reply", response_model=TicketMessageResponse)
def reply_to_ticket(ticket_id: int, msg_in: TicketMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    new_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type="ADMIN",
        message=msg_in.message,
        attachment_url=msg_in.attachment_url,
        is_internal=False
    )
    db.add(new_msg)
    
    ticket.status = "WAITING_FOR_CUSTOMER"
    ticket.updated_at = datetime.utcnow()
    
    # Notify Customer (Stub)
    # print(f"Notify User {ticket.customer_id}: Support replied to your ticket {ticket.ticket_number}.")
    db.commit()
    db.refresh(new_msg)
    return new_msg

@router.post("/{ticket_id}/notes", response_model=TicketInternalNoteResponse)
def add_internal_note(ticket_id: int, note_in: TicketInternalNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    new_note = TicketInternalNote(
        ticket_id=ticket.id,
        admin_id=current_user.id,
        note=note_in.note
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@router.post("/{ticket_id}/close")
def close_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.status = "CLOSED"
    ticket.closed_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Ticket closed successfully"}

@router.post("/{ticket_id}/reopen")
def reopen_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.status = "IN_PROGRESS"
    ticket.closed_at = None
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Ticket reopened successfully"}
