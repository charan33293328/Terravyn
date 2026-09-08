import smtplib
from email.message import EmailMessage
import logging
from database.connection import settings
import os
from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")

def send_invoice_email(customer_email: str, customer_name: str, order_id: str, invoice_number: str, payment_status: str, pdf_path: str):
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        logger.warning("SMTP not configured. Skipping email send.")
        return

    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Order Confirmation - Invoice Attached"
    msg['From'] = settings.SMTP_FROM_EMAIL or "support@terravyn.com"
    msg['To'] = customer_email

    body = f"""Dear {customer_name},

Thank you for choosing TERRAVYN! We have successfully received your order.

Order Details:
- Order ID: {order_id}
- Invoice Number: {invoice_number}
- Payment Status: {payment_status}

Please find your detailed invoice attached to this email.

If you have any questions or need further assistance, please contact us at support@terravyn.com or call +91 800-TERRAVYN.

Best regards,
The TERRAVYN Team
"""
    msg.set_content(body)

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=f"{invoice_number}.pdf")
    else:
        logger.warning(f"PDF path {pdf_path} does not exist. Sending email without attachment.")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Invoice email successfully sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {customer_email}: {str(e)}")

def send_order_status_email(customer_email: str, customer_name: str, order_id: str, status: str, tracking_details: dict = None):
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        logger.warning("SMTP not configured. Skipping status email send.")
        return

    msg = EmailMessage()
    msg['Subject'] = f"TERRAVYN Order Update: {status}"
    msg['From'] = settings.SMTP_FROM_EMAIL or "support@terravyn.com"
    msg['To'] = customer_email

    tracking_section = ""
    if tracking_details and tracking_details.get('courier_name'):
        tracking_section = f"""
Tracking Information:
- Courier: {tracking_details.get('courier_name')}
- Tracking Number: {tracking_details.get('tracking_number') or 'N/A'}
- Tracking URL: {tracking_details.get('tracking_url') or 'N/A'}
- Estimated Delivery: {tracking_details.get('estimated_delivery_date') or 'Pending'}
"""

    body = f"""Dear {customer_name},

Your TERRAVYN order ({order_id}) status has been updated to: {status}.
{tracking_section}
If you have any questions, please contact us at support@terravyn.com or call +91 800-TERRAVYN.

Best regards,
The TERRAVYN Team
"""
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Status email ({status}) successfully sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send status email to {customer_email}: {str(e)}")

def send_otp_email(recipient_email: str, otp: str, recipient_name: str):
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        logger.warning("SMTP not configured. Skipping email send.")
        raise HTTPException(status_code=500, detail="Email service temporarily unavailable.")
        
    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Email Verification Code"
    msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>" if settings.SMTP_FROM_NAME else settings.SMTP_FROM_EMAIL
    msg['To'] = recipient_email

    plain_text = f"Your TERRAVYN verification code is {otp}.\nThis code expires in 10 minutes."
    msg.set_content(plain_text)

    html_body = f"""Hello {recipient_name},<br><br>
Your TERRAVYN verification code is:<br><br>
<h2>{otp}</h2><br>
This verification code will expire in 10 minutes.<br><br>
If you did not request this verification, please ignore this email.<br><br>
Regards,<br>
TERRAVYN Team"""

    msg.add_alternative(html_body, subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"OTP Email Sent successfully to {recipient_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Errors: {str(e)}")
        logger.info(f"MOCK EMAIL: Sent OTP {otp} to {recipient_email}")
    except Exception as e:
        logger.error(f"SMTP Connection Errors: {str(e)}")
        logger.info(f"MOCK EMAIL: Sent OTP {otp} to {recipient_email}")

def send_password_reset_email(recipient_email: str, reset_link: str, recipient_name: str):
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
        logger.warning("SMTP not configured. Skipping email send.")
        raise HTTPException(status_code=500, detail="Email service temporarily unavailable.")
        
    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Password Reset Request"
    msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>" if settings.SMTP_FROM_NAME else settings.SMTP_FROM_EMAIL
    msg['To'] = recipient_email

    plain_text = f"You requested a password reset.\nClick the following link to reset your password: {reset_link}\nThis link expires in 1 hour."
    msg.set_content(plain_text)

    html_body = f"""Hello {recipient_name},<br><br>
You recently requested to reset your password for your TERRAVYN account.<br><br>
Please click the button below to reset it:<br><br>
<a href="{reset_link}" style="display:inline-block;padding:10px 20px;background-color:#10b981;color:#ffffff;text-decoration:none;border-radius:5px;font-weight:bold;">Reset Password</a><br><br>
If you did not request a password reset, please ignore this email or contact support if you have questions.<br><br>
This link will expire in 1 hour.<br><br>
Regards,<br>
TERRAVYN Team"""

    msg.add_alternative(html_body, subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Password Reset Email Sent successfully to {recipient_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to send password reset email. Please try again later.")
    except Exception as e:
        logger.error(f"SMTP Connection Errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Email service temporarily unavailable.")
