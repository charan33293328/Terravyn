import logging
from database.connection import settings
import os
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from fastapi import HTTPException, status
import json
import urllib.request
import urllib.error

logger = logging.getLogger("uvicorn.error")

def validate_email_for_terravyn(email: str) -> str:
    """
    Validates an email address for Terravyn:
    1. Checks for non-empty string.
    2. Validates format and syntax.
    3. Validates domain existence and MX deliverability via DNS.
    Returns normalized email if valid, or raises HTTPException(400) with a user-friendly error message.
    """
    if not email or not isinstance(email, str) or not email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required."
        )
    
    clean_email = email.strip()
    try:
        # check_deliverability=True performs DNS MX lookup
        email_info = validate_email(clean_email, check_deliverability=True)
        return email_info.normalized.lower()
    except EmailSyntaxError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email syntax: {str(e)}"
        )
    except EmailUndeliverableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email domain is invalid or cannot receive mail: {str(e)}"
        )
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email address: {str(e)}"
        )
    except Exception as e:
        logger.warning(f"Email validation error for {_mask_email(clean_email)}: {str(e)}")
        try:
            email_info = validate_email(clean_email, check_deliverability=False)
            return email_info.normalized.lower()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to validate email address: {str(e)}"
            )

def _mask_email(email: str) -> str:
    """Masks email for privacy in logs (e.g. c***@gmail.com)."""
    try:
        parts = email.split("@")
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[0] + "***" if len(name) > 0 else "***"
            return f"{masked_name}@{domain}"
    except Exception:
        pass
    return "recipient"

def _send_http_api_email(recipient_email: str, subject: str, plain_text: str, html_content: str) -> bool:
    """
    Sends transactional email exclusively via HTTPS REST API (Port 443).
    Bypasses cloud provider SMTP firewall blocks completely.
    """
    from_name = (settings.EMAIL_FROM_NAME or settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.EMAIL_FROM or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "onboarding@resend.dev").strip()
    masked_rcpt = _mask_email(recipient_email)
    
    # Check keys
    generic_key = (settings.EMAIL_API_KEY or "").strip()
    resend_key = (settings.RESEND_API_KEY or "").strip() or (generic_key if generic_key.startswith("re_") or not generic_key.startswith(("xkeysib-", "SG.")) else "")
    brevo_key = (settings.BREVO_API_KEY or "").strip() or (generic_key if generic_key.startswith("xkeysib-") else "")
    sendgrid_key = (settings.SENDGRID_API_KEY or "").strip() or (generic_key if generic_key.startswith("SG.") else "")
    
    # 1. Resend API (https://resend.com) - Primary HTTPS Provider (Port 443)
    if resend_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via Resend HTTPS API to {masked_rcpt}...")
            # If from_email is a free public mailbox without custom DNS verification, use Resend's verified test sender
            sender_address = from_email
            if "@gmail.com" in sender_address.lower() or "@yahoo." in sender_address.lower() or "@outlook." in sender_address.lower():
                sender_address = "onboarding@resend.dev"
                
            payload = {
                "from": f"{from_name} <{sender_address}>",
                "to": [recipient_email],
                "subject": subject,
                "text": plain_text,
                "html": html_content
            }
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TERRAVYN/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status in (200, 201):
                    logger.info(f"[EMAIL HTTP SUCCESS] Email accepted and delivered via Resend HTTPS API to {masked_rcpt}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL RESEND ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL RESEND ERROR] {type(e).__name__}: {str(e)}")

    # 2. Brevo API (https://brevo.com / Sendinblue) (Port 443)
    if brevo_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via Brevo HTTPS API to {masked_rcpt}...")
            payload = {
                "sender": {"name": from_name, "email": from_email},
                "to": [{"email": recipient_email}],
                "subject": subject,
                "textContent": plain_text,
                "htmlContent": html_content
            }
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "api-key": brevo_key,
                    "Content-Type": "application/json",
                    "User-Agent": "TERRAVYN/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status in (200, 201):
                    logger.info(f"[EMAIL HTTP SUCCESS] Email accepted and delivered via Brevo HTTPS API to {masked_rcpt}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL BREVO ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL BREVO ERROR] {type(e).__name__}: {str(e)}")

    # 3. SendGrid API (Port 443)
    if sendgrid_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via SendGrid HTTPS API to {masked_rcpt}...")
            payload = {
                "personalizations": [{"to": [{"email": recipient_email}]}],
                "from": {"email": from_email, "name": from_name},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": plain_text},
                    {"type": "text/html", "value": html_content}
                ]
            }
            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {sendgrid_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TERRAVYN/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status in (200, 202):
                    logger.info(f"[EMAIL HTTP SUCCESS] Email accepted and delivered via SendGrid HTTPS API to {masked_rcpt}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL SENDGRID ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL SENDGRID ERROR] {type(e).__name__}: {str(e)}")

    if not (resend_key or brevo_key or sendgrid_key or generic_key):
        logger.error("[EMAIL CONFIG ERROR] No HTTPS Email API Key configured. Please set RESEND_API_KEY or EMAIL_API_KEY in Render Environment.")
    
    return False

def _dispatch_email(recipient_email: str, subject: str, plain_text: str, html_content: str = "") -> bool:
    """Dispatches email exclusively via HTTPS REST API (Port 443)."""
    return _send_http_api_email(recipient_email, subject, plain_text, html_content)

def send_invoice_email(customer_email: str, customer_name: str, order_id: str, invoice_number: str, payment_status: str, pdf_path: str = None) -> bool:
    from_name = (settings.EMAIL_FROM_NAME or settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.EMAIL_FROM or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()
    subject = "TERRAVYN Order Confirmation - Invoice Details"

    body = f"""Dear {customer_name},

Thank you for choosing TERRAVYN! We have successfully received your order.

Order Details:
- Order ID: {order_id}
- Invoice Number: {invoice_number}
- Payment Status: {payment_status}

If you have any questions or need further assistance, please contact us at support@terravyn.com or call +91 800-TERRAVYN.

Best regards,
The TERRAVYN Team
"""
    return _dispatch_email(customer_email, subject, body, "")

def send_order_status_email(customer_email: str, customer_name: str, order_id: str, status: str, tracking_details: dict = None) -> bool:
    from_name = (settings.EMAIL_FROM_NAME or settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.EMAIL_FROM or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()
    subject = f"TERRAVYN Order Update: {status}"

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
    return _dispatch_email(customer_email, subject, body, "")

def send_otp_email(recipient_email: str, otp: str, recipient_name: str) -> bool:
    subject = "TERRAVYN Email Verification Code"
    plain_text = f"Hello {recipient_name},\n\nYour TERRAVYN verification code is: {otp}\n\nThis code expires in 10 minutes.\nIf you did not request this code, please ignore this email.\n\nBest regards,\nTERRAVYN Team"
    
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
  <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
    <h2 style="color: #10b981; margin-top: 0;">TERRAVYN Verification</h2>
    <p>Hello <strong>{recipient_name}</strong>,</p>
    <p>Your verification code for creating your TERRAVYN account is:</p>
    <div style="text-align: center; margin: 24px 0;">
      <span style="display: inline-block; font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #0f172a; background-color: #f1f5f9; padding: 12px 24px; border-radius: 8px; border: 1px dashed #94a3b8;">{otp}</span>
    </div>
    <p style="font-size: 13px; color: #64748b;">This verification code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
    <p style="font-size: 12px; color: #94a3b8; margin-bottom: 0;">Regards,<br><strong>TERRAVYN Smart Agriculture</strong></p>
  </div>
</body>
</html>"""

    return _dispatch_email(recipient_email, subject, plain_text, html_body)

def send_password_reset_email(recipient_email: str, reset_link: str, recipient_name: str) -> bool:
    subject = "TERRAVYN Password Reset Request"
    plain_text = f"Hello {recipient_name},\n\nYou requested a password reset for your TERRAVYN account.\nClick the following link to reset your password: {reset_link}\nThis link expires in 1 hour.\n\nBest regards,\nTERRAVYN Team"
    
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
  <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
    <h2 style="color: #10b981; margin-top: 0;">Reset Your Password</h2>
    <p>Hello <strong>{recipient_name}</strong>,</p>
    <p>You recently requested to reset your password for your TERRAVYN account. Click the button below to proceed:</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{reset_link}" style="display: inline-block; padding: 12px 28px; background-color: #10b981; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;">Reset Password</a>
    </div>
    <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br><a href="{reset_link}" style="color: #10b981; word-break: break-all;">{reset_link}</a></p>
    <p style="font-size: 13px; color: #64748b;">This link will expire in 1 hour. If you did not request a password reset, you can safely ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
    <p style="font-size: 12px; color: #94a3b8; margin-bottom: 0;">Regards,<br><strong>TERRAVYN Smart Agriculture</strong></p>
  </div>
</body>
</html>"""

    return _dispatch_email(recipient_email, subject, plain_text, html_body)

