import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = Path(__file__).resolve().parent.parent
INVOICE_DIR = os.path.join(BASE_DIR, "uploads", "invoices")

def ensure_invoice_dir():
    if not os.path.exists(INVOICE_DIR):
        os.makedirs(INVOICE_DIR)

def generate_invoice_pdf(invoice) -> str:
    ensure_invoice_dir()
    file_path = os.path.join(INVOICE_DIR, f"{invoice.invoice_number}.pdf")
    
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#16a34a'), # Brand Color
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        spaceAfter=2
    )

    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=2
    )

    # Header
    elements.append(Paragraph("TERRAVYN", title_style))
    elements.append(Paragraph("SUHARA Global Groups Pvt. Ltd.", bold_style))
    elements.append(Paragraph("123 Agri-Tech Park, Innovation Hub", header_style))
    elements.append(Paragraph("GSTIN: 29ABCDE1234F1Z5", header_style))
    elements.append(Paragraph("Email: support@terravyn.com", header_style))
    elements.append(Paragraph("Phone: +91 800-TERRAVYN", header_style))
    elements.append(Spacer(1, 20))
    
    # Title
    elements.append(Paragraph("TAX INVOICE", ParagraphStyle('SubTitle', parent=styles['Heading2'], alignment=1)))
    elements.append(Spacer(1, 10))
    
    # Customer and Order Details Table
    customer_info = [
        ["Invoice Number:", invoice.invoice_number, "Customer Name:", invoice.customer_name],
        ["Order ID:", invoice.order_id, "Phone:", invoice.phone],
        ["Invoice Date:", invoice.invoice_date.strftime("%Y-%m-%d %H:%M"), "Email:", invoice.email],
        ["Payment Method:", invoice.payment_method, "Billing Address:", invoice.billing_address],
        ["Payment Status:", invoice.payment_status, "", ""]
    ]
    
    t_info = Table(customer_info, colWidths=[100, 150, 100, 150])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    
    # Products Table
    data = [
        ["Product Name", "Quantity", "Unit Price (₹)", "Subtotal (₹)"]
    ]
    data.append([
        invoice.product_name,
        str(invoice.quantity),
        f"{invoice.unit_price:,.2f}",
        f"{invoice.subtotal:,.2f}"
    ])
    
    t_prod = Table(data, colWidths=[250, 70, 90, 90])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(t_prod)
    elements.append(Spacer(1, 15))
    
    # Summary
    summary_data = [
        ["", "", "Subtotal:", f"₹ {invoice.subtotal:,.2f}"],
        ["", "", f"GST ({invoice.gst_percentage}%):", f"₹ {invoice.gst_amount:,.2f}"],
        ["", "", "Grand Total:", f"₹ {invoice.total_amount:,.2f}"]
    ]
    t_summary = Table(summary_data, colWidths=[200, 100, 100, 100])
    t_summary.setStyle(TableStyle([
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2,-1), (-1,-1), colors.HexColor('#16a34a')),
        ('FONTSIZE', (2,-1), (-1,-1), 12),
        ('LINEABOVE', (2,-1), (-1,-1), 1, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 40))
    
    # Footer
    elements.append(Paragraph("Thank you for choosing TERRAVYN.", ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, fontName='Helvetica-Oblique')))
    
    doc.build(elements)
    return file_path
