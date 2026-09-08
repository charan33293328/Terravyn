from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import os

from database.connection import get_db
from models.domain import User, Farmer, SupportTicket, TicketMessage, TicketAttachment
from auth.security import get_current_active_user
from schemas.support import SupportTicketResponse, SupportTicketDetailResponse, SupportTicketSummary, PaginatedTicketsResponse
from services.storage import storage_provider

router = APIRouter()

def get_farmer(db: Session, current_user: User):
    farmer = db.query(Farmer).filter(
        (Farmer.email == current_user.email) | 
        (Farmer.phone == current_user.phone_number)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer

def generate_ticket_number(db: Session) -> str:
    today = datetime.utcnow()
    prefix = f"TKT-{today.year}-"
    
    # Get highest ticket number for current year
    last_ticket = db.query(SupportTicket).filter(
        SupportTicket.ticket_number.like(f"{prefix}%")
    ).order_by(desc(SupportTicket.id)).first()
    
    if last_ticket and last_ticket.ticket_number:
        try:
            sequence = int(last_ticket.ticket_number.split("-")[-1]) + 1
        except:
            sequence = 1
    else:
        sequence = 1
        
    return f"{prefix}{sequence:06d}"

@router.get("/api/farmer/support/summary", response_model=SupportTicketSummary)
def get_support_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    query = db.query(SupportTicket).filter(SupportTicket.farmer_id == farmer.id)
    
    total = query.count()
    open_count = query.filter(SupportTicket.status.in_(["OPEN", "IN_PROGRESS", "AWAITING_FARMER_RESPONSE"])).count()
    resolved_count = query.filter(SupportTicket.status == "RESOLVED").count()
    closed_count = query.filter(SupportTicket.status == "CLOSED").count()
    
    return SupportTicketSummary(
        total_tickets=total,
        open_tickets=open_count,
        resolved_tickets=resolved_count,
        closed_tickets=closed_count
    )

@router.get("/api/farmer/support/tickets", response_model=PaginatedTicketsResponse)
def get_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    query = db.query(SupportTicket).filter(SupportTicket.farmer_id == farmer.id)
    
    if status and status.upper() != "ALL":
        query = query.filter(SupportTicket.status == status.upper())
    
    if priority and priority.upper() != "ALL":
        query = query.filter(SupportTicket.priority == priority.upper())
        
    if category and category.upper() != "ALL":
        query = query.filter(SupportTicket.category == category)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (SupportTicket.ticket_number.ilike(search_term)) |
            (SupportTicket.subject.ilike(search_term)) |
            (SupportTicket.category.ilike(search_term))
        )
        
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    tickets = query.order_by(desc(SupportTicket.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedTicketsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        tickets=tickets
    )

@router.get("/api/farmer/support/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
def get_ticket_details(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.farmer_id == farmer.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    return ticket

@router.post("/api/farmer/support/tickets", response_model=SupportTicketResponse)
async def create_ticket(
    subject: str = Form(...),
    description: str = Form(...),
    category: str = Form("GENERAL_INQUIRY"),
    priority: str = Form("NORMAL"),
    device_id: Optional[int] = Form(None),
    farm_id: Optional[int] = Form(None),
    order_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    # 1. Validation
    if files and len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per ticket.")
        
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if files:
        for f in files:
            if f.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail=f"File type {f.content_type} not allowed.")
    
    # 2. Create Ticket
    ticket_number = generate_ticket_number(db)
    new_ticket = SupportTicket(
        ticket_number=ticket_number,
        customer_id=current_user.id,
        farmer_id=farmer.id,
        device_id=device_id,
        farm_id=farm_id,
        order_id=order_id,
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        status="OPEN"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # 3. Create Initial Message
    initial_msg = TicketMessage(
        ticket_id=new_ticket.id,
        sender_id=current_user.id,
        sender_type="FARMER",
        message=description,
        is_internal=False
    )
    db.add(initial_msg)
    db.commit()
    db.refresh(initial_msg)
    
    # 4. Handle Uploads
    if files:
        directory = f"support/tickets/{new_ticket.ticket_number}"
        for f in files:
            meta = await storage_provider.save_file(f, directory, "TKT")
            attachment = TicketAttachment(
                ticket_id=new_ticket.id,
                message_id=initial_msg.id,
                file_name=meta["original_filename"],
                stored_file_name=meta["stored_filename"],
                file_path=meta["file_path"],
                file_size=meta["file_size"],
                mime_type=meta["mime_type"],
                uploaded_by=current_user.id
            )
            db.add(attachment)
        db.commit()

    db.refresh(new_ticket)
    return new_ticket

@router.post("/api/farmer/support/tickets/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: int,
    message: str = Form(...),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.farmer_id == farmer.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    if ticket.status in ["RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="Cannot reply to a resolved or closed ticket.")
        
    # Validation
    if files and len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per reply.")
        
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if files:
        for f in files:
            if f.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail=f"File type {f.content_type} not allowed.")
                
    # Create Message
    new_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_type="FARMER",
        message=message,
        is_internal=False
    )
    db.add(new_msg)
    
    # Update Ticket Status
    ticket.status = "OPEN" # Move back to OPEN if awaiting response
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_msg)
    
    # Handle Uploads
    if files:
        directory = f"support/tickets/{ticket.ticket_number}"
        for f in files:
            meta = await storage_provider.save_file(f, directory, "TKT")
            attachment = TicketAttachment(
                ticket_id=ticket.id,
                message_id=new_msg.id,
                file_name=meta["original_filename"],
                stored_file_name=meta["stored_filename"],
                file_path=meta["file_path"],
                file_size=meta["file_size"],
                mime_type=meta["mime_type"],
                uploaded_by=current_user.id
            )
            db.add(attachment)
        db.commit()
        
    return {"status": "success", "message": "Reply sent successfully"}

@router.put("/api/farmer/support/tickets/{ticket_id}/close")
def close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.farmer_id == farmer.id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    if ticket.status not in ["RESOLVED", "AWAITING_FARMER_RESPONSE"]:
        raise HTTPException(status_code=400, detail="Ticket cannot be closed from current status.")
        
    ticket.status = "CLOSED"
    ticket.closed_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    return {"status": "success", "message": "Ticket closed successfully"}

from fastapi.responses import FileResponse

@router.get("/api/farmer/support/attachments/{attachment_id}")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    # Validate ownership: Farmer must own the ticket
    attachment = db.query(TicketAttachment).join(SupportTicket).filter(
        TicketAttachment.id == attachment_id,
        SupportTicket.farmer_id == farmer.id
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found or access denied.")
        
    file_path = storage_provider.get_file_path(attachment.file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server.")
        
    return FileResponse(
        path=file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type
    )
