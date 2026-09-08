import smtplib
from email.message import EmailMessage
import logging
from database.connection import settings
import os
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from fastapi import HTTPException, status

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
        logger.warning(f"Email validation error for {clean_email}: {str(e)}")
        try:
            email_info = validate_email(clean_email, check_deliverability=False)
            return email_info.normalized.lower()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to validate email address: {str(e)}"
            )


import socket
import ssl
import json
import urllib.request
import urllib.error

def _send_http_api_email(recipient_email: str, subject: str, plain_text: str, html_content: str) -> bool:
    """
    Sends transactional email via HTTPS REST API (Port 443).
    Supported by cloud runtimes (Render, Vercel, AWS, etc.) where outbound SMTP ports (25, 465, 587) are blocked.
    """
    from_name = (settings.EMAIL_FROM_NAME or settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.EMAIL_FROM or settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "onboarding@resend.dev").strip()
    
    # Check keys
    generic_key = (settings.EMAIL_API_KEY or "").strip()
    resend_key = (settings.RESEND_API_KEY or "").strip() or (generic_key if generic_key.startswith("re_") or not generic_key.startswith(("xkeysib-", "SG.")) else "")
    brevo_key = (settings.BREVO_API_KEY or "").strip() or (generic_key if generic_key.startswith("xkeysib-") else "")
    sendgrid_key = (settings.SENDGRID_API_KEY or "").strip() or (generic_key if generic_key.startswith("SG.") else "")
    
    # 1. Resend API (https://resend.com) - Primary HTTPS Provider
    if resend_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via Resend API to {recipient_email}...")
            # If from_email is a standard gmail address and domain isn't verified on Resend, Resend requires onboarding@resend.dev for testing
            sender_address = from_email
            if "@gmail.com" in sender_address.lower() or "@yahoo." in sender_address.lower():
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
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status in (200, 201):
                    logger.info(f"[EMAIL HTTP SUCCESS] Verification email delivered via Resend to {recipient_email}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL RESEND ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL RESEND ERROR] {type(e).__name__}: {str(e)}")

    # 2. Brevo API (https://brevo.com / Sendinblue)
    if brevo_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via Brevo API to {recipient_email}...")
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
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status in (200, 201):
                    logger.info(f"[EMAIL HTTP SUCCESS] Verification email delivered via Brevo to {recipient_email}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL BREVO ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL BREVO ERROR] {type(e).__name__}: {str(e)}")

    # 3. SendGrid API
    if sendgrid_key:
        try:
            logger.info(f"[EMAIL HTTP API] Dispatching email via SendGrid API to {recipient_email}...")
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
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status in (200, 202):
                    logger.info(f"[EMAIL HTTP SUCCESS] Verification email delivered via SendGrid to {recipient_email}")
                    return True
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            logger.error(f"[EMAIL SENDGRID ERROR] HTTP {http_err.code}: {err_body}")
        except Exception as e:
            logger.error(f"[EMAIL SENDGRID ERROR] {type(e).__name__}: {str(e)}")

    return False

def _send_smtp_message(msg: EmailMessage, recipient_email: str) -> bool:
    host = (settings.SMTP_HOST or "").strip()
    username = (settings.SMTP_USERNAME or "").strip()
    # Strip spaces that users commonly copy with Google App Passwords (e.g. "abcd efgh ijkl mnop")
    password = (settings.SMTP_PASSWORD or "").replace(" ", "").strip()
    
    if not host or not username:
        logger.warning(f"[SMTP UNCONFIGURED] Missing SMTP_HOST or SMTP_USERNAME. Cannot send email to {recipient_email}")
        return False
        
    try:
        configured_port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
    except (ValueError, TypeError):
        configured_port = 587

    # Strategies to try in order: (use_ssl, port)
    if configured_port == 465:
        strategies = [(True, 465), (False, 587), (False, 2525)]
    elif configured_port == 2525:
        strategies = [(False, 2525), (False, 587), (True, 465)]
    else:
        strategies = [(False, configured_port), (True, 465), (False, 2525)]

    last_error_stage = None
    last_error_message = None

    for use_ssl, try_port in strategies:
        try:
            logger.info(f"[SMTP ATTEMPT] stage=CONNECT host={host} port={try_port} ssl={use_ssl}")
            
            # Step 1: TCP Socket connection
            if use_ssl:
                server = smtplib.SMTP_SSL(host, try_port, timeout=12)
            else:
                server = smtplib.SMTP(host, try_port, timeout=12)
                server.ehlo()
                
                # Step 2: STARTTLS negotiation
                if settings.SMTP_USE_TLS or try_port == 587:
                    server.starttls()
                    server.ehlo()
            
            # Step 3: SMTP Authentication & Send
            with server:
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"[SMTP SUCCESS] Email successfully delivered to {recipient_email} via {host}:{try_port}")
            return True

        except socket.gaierror as dns_err:
            last_error_stage = "DNS_RESOLUTION"
            last_error_message = f"DNS lookup failed for host '{host}': {str(dns_err)}"
            logger.error(f"[SMTP DNS FAILED] stage={last_error_stage} host={host} error={str(dns_err)}")
            break # No point retrying other ports if DNS fails

        except smtplib.SMTPAuthenticationError as auth_err:
            last_error_stage = "SMTP_AUTH"
            last_error_message = f"Authentication rejected by {host}:{try_port}. Verify email credentials/App Password."
            logger.error(f"[SMTP AUTH FAILED] stage={last_error_stage} host={host} port={try_port} error={auth_err.smtp_code} {auth_err.smtp_error}")
            break # Credentials invalid, no need to retry

        except (socket.timeout, TimeoutError) as timeout_err:
            last_error_stage = "TCP_TIMEOUT"
            last_error_message = f"Connection to {host}:{try_port} timed out."
            logger.warning(f"[SMTP TIMEOUT] stage={last_error_stage} host={host} port={try_port}")

        except OSError as net_err:
            last_error_stage = "NETWORK_UNREACHABLE"
            last_error_message = f"Network unreachable to {host}:{try_port} (Outbound SMTP port blocked by host/environment): {str(net_err)}"
            logger.warning(f"[SMTP NETWORK FAILED] stage={last_error_stage} host={host} port={try_port} error={str(net_err)}")

        except Exception as e:
            last_error_stage = type(e).__name__
            last_error_message = str(e)
            logger.warning(f"[SMTP ERROR] stage={last_error_stage} host={host} port={try_port} error={str(e)}")

    logger.error(f"[SMTP DELIVERY FAILED] recipient={recipient_email} stage={last_error_stage} error={last_error_message}")
    return False

def _dispatch_email(msg: EmailMessage, recipient_email: str, subject: str, plain_text: str, html_content: str) -> bool:
    """Dispatches email via HTTPS API if configured, otherwise falls back to SMTP."""
    if settings.RESEND_API_KEY or settings.BREVO_API_KEY or settings.SENDGRID_API_KEY:
        if _send_http_api_email(recipient_email, subject, plain_text, html_content):
            return True
    return _send_smtp_message(msg, recipient_email)

def send_invoice_email(customer_email: str, customer_name: str, order_id: str, invoice_number: str, payment_status: str, pdf_path: str):
    from_name = (settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()

    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Order Confirmation - Invoice Attached"
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = customer_email
    msg['Reply-To'] = from_email

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

    _send_smtp_message(msg, customer_email)

def send_order_status_email(customer_email: str, customer_name: str, order_id: str, status: str, tracking_details: dict = None):
    from_name = (settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()

    msg = EmailMessage()
    msg['Subject'] = f"TERRAVYN Order Update: {status}"
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = customer_email
    msg['Reply-To'] = from_email

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
    _send_smtp_message(msg, customer_email)

def send_otp_email(recipient_email: str, otp: str, recipient_name: str) -> bool:
    from_name = (settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()

    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Email Verification Code"
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = recipient_email
    msg['Reply-To'] = from_email

    plain_text = f"Hello {recipient_name},\n\nYour TERRAVYN verification code is: {otp}\n\nThis code expires in 10 minutes.\nIf you did not request this code, please ignore this email.\n\nBest regards,\nTERRAVYN Team"
    msg.set_content(plain_text)

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

    msg.add_alternative(html_body, subtype='html')
    return _dispatch_email(msg, recipient_email, msg['Subject'], plain_text, html_body)

def send_password_reset_email(recipient_email: str, reset_link: str, recipient_name: str) -> bool:
    from_name = (settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    from_email = (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "support@terravyn.com").strip()

    msg = EmailMessage()
    msg['Subject'] = "TERRAVYN Password Reset Request"
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = recipient_email
    msg['Reply-To'] = from_email

    plain_text = f"Hello {recipient_name},\n\nYou requested a password reset for your TERRAVYN account.\nClick the following link to reset your password: {reset_link}\nThis link expires in 1 hour.\n\nBest regards,\nTERRAVYN Team"
    msg.set_content(plain_text)

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

    msg.add_alternative(html_body, subtype='html')
    return _dispatch_email(msg, recipient_email, msg['Subject'], plain_text, html_body)

