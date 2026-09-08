from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from models.domain import Invoice
from schemas.domain import InvoiceResponse
from services.invoice_generator import generate_invoice_pdf
import os
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

def get_invoice_pdf_path(db: Session, invoice: Invoice) -> str:
    """Helper to resolve path, verify existence, and auto-regenerate if missing."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Check if we have a path stored
    if invoice.invoice_pdf_path:
        # Determine if stored path is relative or absolute
        stored_path = Path(invoice.invoice_pdf_path)
        if not stored_path.is_absolute():
            absolute_path = base_dir / stored_path
        else:
            absolute_path = stored_path
            
        logger.info(f"Invoice Request: {invoice.invoice_number}")
        logger.info(f"Database Path: {invoice.invoice_pdf_path}")
        logger.info(f"Resolved Absolute Path: {absolute_path}")
        
        if absolute_path.exists():
            logger.info("File Exists Status: True")
            return str(absolute_path)
        else:
            logger.warning("File Exists Status: False (File missing on disk)")
            
    # Auto-Regeneration Triggered
    logger.info(f"Regeneration Attempts: 1 for invoice {invoice.invoice_number}")
    try:
        new_pdf_path = generate_invoice_pdf(invoice)
        invoice.invoice_pdf_path = new_pdf_path
        db.commit()
        db.refresh(invoice)
        logger.info(f"Successfully regenerated invoice PDF at {new_pdf_path}")
        return new_pdf_path
    except Exception as e:
        logger.error(f"Failed to regenerate PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to generate invoice PDF.")


@router.get("/{order_id}", response_model=InvoiceResponse)
def get_invoice(order_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/{order_id}/view")
def view_invoice(order_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_path = get_invoice_pdf_path(db, invoice)
    
    logger.info(f"Download Success: Viewing {invoice.invoice_number}")
    return FileResponse(
        path=pdf_path, 
        filename=f"{invoice.invoice_number}.pdf",
        media_type="application/pdf",
        content_disposition_type="inline"
    )

@router.get("/{order_id}/download")
def download_invoice(order_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_path = get_invoice_pdf_path(db, invoice)
    
    logger.info(f"Download Success: Downloading {invoice.invoice_number}")
    return FileResponse(
        path=pdf_path, 
        filename=f"{invoice.invoice_number}.pdf",
        media_type="application/pdf",
        content_disposition_type="attachment"
    )
