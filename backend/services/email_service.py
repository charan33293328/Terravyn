import logging
import os
import socket
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr, formatdate, make_msgid
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
from fastapi import HTTPException, status

from database.connection import settings

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

def _send_smtp_email(
    recipient_email: str,
    subject: str,
    plain_text: str,
    html_content: str = "",
    attachment_path: str = None
) -> bool:
    """
    Sends transactional email via standard SMTP.
    Configurable via environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME, SMTP_USE_TLS, SMTP_USE_SSL, SMTP_TIMEOUT).
    """
    host = (settings.SMTP_HOST or "").strip()
    port = settings.SMTP_PORT or 587
    username = (settings.SMTP_USERNAME or "").strip()
    password = (settings.SMTP_PASSWORD or "").strip()
    from_email = (settings.SMTP_FROM_EMAIL or username or "no-reply@terravyn.com").strip()
    from_name = (settings.SMTP_FROM_NAME or "TERRAVYN").strip()
    use_tls = bool(settings.SMTP_USE_TLS)
    use_ssl = bool(settings.SMTP_USE_SSL)
    timeout = settings.SMTP_TIMEOUT or 15
    masked_rcpt = _mask_email(recipient_email)

    if not host:
        logger.error("[EMAIL SMTP CONFIG ERROR] SMTP_HOST is not configured in environment variables.")
        return False

    if not from_email:
        logger.error("[EMAIL SMTP CONFIG ERROR] SMTP_FROM_EMAIL (or SMTP_USERNAME) is not configured in environment variables.")
        return False

    # Create base MIME container
    if attachment_path and os.path.isfile(attachment_path):
        msg = MIMEMultipart("mixed")
        body_container = MIMEMultipart("alternative")
        msg.attach(body_container)
    else:
        msg = MIMEMultipart("alternative")
        body_container = msg

    # Set MIME headers
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)
    domain_part = from_email.split("@")[-1] if "@" in from_email else None
    msg["Message-ID"] = make_msgid(domain=domain_part)

    # Attach plain text and HTML alternatives
    if plain_text:
        body_container.attach(MIMEText(plain_text, "plain", "utf-8"))
    if html_content:
        body_container.attach(MIMEText(html_content, "html", "utf-8"))
    if not plain_text and not html_content:
        body_container.attach(MIMEText(subject, "plain", "utf-8"))

    # Attach file if provided and exists
    if attachment_path and os.path.isfile(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
        except Exception as e:
            logger.warning(f"[EMAIL SMTP ATTACHMENT WARNING] Could not attach file {attachment_path}: {str(e)}")

    server = None
    try:
        logger.info(f"[EMAIL SMTP] SMTP email dispatch initiated to {masked_rcpt} via {host}:{port}...")

        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=timeout)
            server.ehlo()
        else:
            server = smtplib.SMTP(host=host, port=port, timeout=timeout)
            server.ehlo()
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

        if username and password:
            server.login(username, password)

        server.send_message(msg)
        logger.info(f"[EMAIL SMTP] SMTP email accepted by host for {masked_rcpt}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(f"[EMAIL SMTP AUTH ERROR] Authentication failed on {host}:{port}. Check SMTP_USERNAME and SMTP_PASSWORD.")
    except smtplib.SMTPConnectError as e:
        logger.error(f"[EMAIL SMTP CONNECT ERROR] Failed to connect to {host}:{port}: {str(e)}")
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"[EMAIL SMTP DISCONNECT ERROR] SMTP server disconnected unexpectedly ({host}:{port}): {str(e)}")
    except smtplib.SMTPResponseException as e:
        logger.error(f"[EMAIL SMTP RESPONSE ERROR] SMTP server responded with code {e.smtp_code}: {e.smtp_error}")
    except ssl.SSLError as e:
        logger.error(f"[EMAIL SMTP SSL ERROR] SSL/TLS handshake failed on {host}:{port}: {str(e)}")
    except (socket.timeout, TimeoutError):
        logger.error(f"[EMAIL SMTP TIMEOUT] SMTP connection or response timed out ({timeout}s) for {host}:{port}")
    except OSError as e:
        err_msg = str(e)
        if e.errno in (101, 10051):
            logger.error(f"[EMAIL SMTP NETWORK UNREACHABLE] [Errno {e.errno}] Network is unreachable connecting to {host}:{port}. Host outbound SMTP traffic blocked.")
        else:
            logger.error(f"[EMAIL SMTP OS ERROR] [Errno {e.errno}] Failed to connect to {host}:{port}: {err_msg}")
    except Exception as e:
        logger.error(f"[EMAIL SMTP UNEXPECTED ERROR] {type(e).__name__}: {str(e)}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass

    return False

def test_smtp_connection() -> dict:
    """
    Safely tests the configured SMTP server without logging credentials or sending real emails.
    Verifies DNS resolution, TCP connectivity, TLS/SSL negotiation, and authentication.
    """
    host = (settings.SMTP_HOST or "").strip()
    port = settings.SMTP_PORT or 587
    username = (settings.SMTP_USERNAME or "").strip()
    password = (settings.SMTP_PASSWORD or "").strip()
    use_tls = bool(settings.SMTP_USE_TLS)
    use_ssl = bool(settings.SMTP_USE_SSL)
    timeout = settings.SMTP_TIMEOUT or 10

    results = {
        "configured_host": host or "NOT CONFIGURED",
        "configured_port": port,
        "security_mode": "SSL" if use_ssl else ("STARTTLS" if use_tls else "PLAIN"),
        "dns": {"status": "NOT_RUN", "resolved_ips": [], "error": None},
        "tcp": {"status": "NOT_RUN", "error": None},
        "tls_ssl": {"status": "NOT_RUN", "error": None},
        "auth": {"status": "NOT_RUN", "error": None},
        "overall_status": "FAIL",
        "summary": ""
    }

    if not host:
        results["summary"] = "SMTP_HOST is not configured in environment variables."
        return results

    # 1. DNS Resolution
    try:
        ips = socket.gethostbyname_ex(host)
        results["dns"]["status"] = "PASS"
        results["dns"]["resolved_ips"] = ips[2]
    except Exception as e:
        results["dns"]["status"] = "FAIL"
        results["dns"]["error"] = str(e)
        results["summary"] = f"DNS resolution failed for {host}: {str(e)}"
        return results

    # 2. TCP Connection & Protocol Handshake
    server = None
    try:
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=timeout)
            results["tcp"]["status"] = "PASS"
            results["tls_ssl"]["status"] = "PASS"
            server.ehlo()
        else:
            server = smtplib.SMTP(host=host, port=port, timeout=timeout)
            results["tcp"]["status"] = "PASS"
            server.ehlo()
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()
                results["tls_ssl"]["status"] = "PASS"
            else:
                results["tls_ssl"]["status"] = "SKIPPED (Plain SMTP)"

        # 3. Authentication Check
        if username and password:
            server.login(username, password)
            results["auth"]["status"] = "PASS"
        else:
            results["auth"]["status"] = "SKIPPED (No credentials provided)"

        results["overall_status"] = "PASS"
        results["summary"] = f"Successfully connected and authenticated with SMTP host {host}:{port}"

    except smtplib.SMTPAuthenticationError:
        results["auth"]["status"] = "FAIL"
        results["auth"]["error"] = "Authentication failed. Please verify SMTP_USERNAME and SMTP_PASSWORD."
        results["summary"] = "SMTP authentication failed."
    except ssl.SSLError as e:
        results["tls_ssl"]["status"] = "FAIL"
        results["tls_ssl"]["error"] = f"SSL/TLS error: {str(e)}"
        results["summary"] = f"TLS/SSL handshake failed with {host}:{port}"
    except (socket.timeout, TimeoutError):
        results["tcp"]["status"] = "FAIL"
        results["tcp"]["error"] = f"Connection timed out ({timeout}s)"
        results["summary"] = f"Connection to {host}:{port} timed out."
    except OSError as e:
        results["tcp"]["status"] = "FAIL"
        if e.errno in (101, 10051):
            results["tcp"]["error"] = f"[Errno {e.errno}] Network unreachable. Outbound SMTP blocked by hosting environment."
            results["summary"] = "Hosting environment network blocks outbound SMTP traffic."
        else:
            results["tcp"]["error"] = str(e)
            results["summary"] = f"Failed to connect to {host}:{port}: {str(e)}"
    except Exception as e:
        results["summary"] = f"SMTP diagnostic encountered {type(e).__name__}: {str(e)}"
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass

    return results

def _dispatch_email(
    recipient_email: str,
    subject: str,
    plain_text: str,
    html_content: str = "",
    attachment_path: str = None
) -> bool:
    """Dispatches email via standard configurable SMTP."""
    return _send_smtp_email(recipient_email, subject, plain_text, html_content, attachment_path)

def send_invoice_email(
    customer_email: str,
    customer_name: str,
    order_id: str,
    invoice_number: str,
    payment_status: str,
    pdf_path: str = None
) -> bool:
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

    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
  <div style="max-width: 550px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
    <h2 style="color: #10b981; margin-top: 0;">Order Confirmation</h2>
    <p>Dear <strong>{customer_name}</strong>,</p>
    <p>Thank you for choosing TERRAVYN! We have successfully received your order.</p>
    
    <div style="background-color: #f1f5f9; border-radius: 8px; padding: 16px; margin: 20px 0;">
      <p style="margin: 4px 0;"><strong>Order ID:</strong> {order_id}</p>
      <p style="margin: 4px 0;"><strong>Invoice Number:</strong> {invoice_number}</p>
      <p style="margin: 4px 0;"><strong>Payment Status:</strong> {payment_status}</p>
    </div>
    
    <p style="font-size: 13px; color: #64748b;">If you have any questions or need further assistance, please contact us at support@terravyn.com.</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
    <p style="font-size: 12px; color: #94a3b8; margin-bottom: 0;">Regards,<br><strong>TERRAVYN Smart Agriculture</strong></p>
  </div>
</body>
</html>"""

    return _dispatch_email(customer_email, subject, body, html_body, pdf_path)

def send_order_status_email(
    customer_email: str,
    customer_name: str,
    order_id: str,
    status: str,
    tracking_details: dict = None
) -> bool:
    subject = f"TERRAVYN Order Update: {status}"

    tracking_section_text = ""
    tracking_section_html = ""
    if tracking_details and tracking_details.get("courier_name"):
        courier = tracking_details.get("courier_name")
        trk_num = tracking_details.get("tracking_number") or "N/A"
        trk_url = tracking_details.get("tracking_url") or "N/A"
        est_del = tracking_details.get("estimated_delivery_date") or "Pending"

        tracking_section_text = f"""
Tracking Information:
- Courier: {courier}
- Tracking Number: {trk_num}
- Tracking URL: {trk_url}
- Estimated Delivery: {est_del}
"""
        tracking_section_html = f"""
        <div style="background-color: #f1f5f9; border-radius: 8px; padding: 16px; margin: 20px 0;">
          <h4 style="margin: 0 0 10px 0; color: #334155;">Tracking Information</h4>
          <p style="margin: 4px 0;"><strong>Courier:</strong> {courier}</p>
          <p style="margin: 4px 0;"><strong>Tracking Number:</strong> {trk_num}</p>
          <p style="margin: 4px 0;"><strong>Estimated Delivery:</strong> {est_del}</p>
          {f'<p style="margin: 4px 0;"><a href="{trk_url}" style="color: #10b981; font-weight: bold;">Track Package</a></p>' if trk_url != 'N/A' else ''}
        </div>
        """

    body = f"""Dear {customer_name},

Your TERRAVYN order ({order_id}) status has been updated to: {status}.
{tracking_section_text}
If you have any questions, please contact us at support@terravyn.com or call +91 800-TERRAVYN.

Best regards,
The TERRAVYN Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; color: #1e293b;">
  <div style="max-width: 550px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
    <h2 style="color: #10b981; margin-top: 0;">Order Status Update</h2>
    <p>Dear <strong>{customer_name}</strong>,</p>
    <p>Your TERRAVYN order <strong>{order_id}</strong> status has been updated to: <strong style="color: #10b981;">{status}</strong>.</p>
    {tracking_section_html}
    <p style="font-size: 13px; color: #64748b;">If you have any questions or need further assistance, please contact us at support@terravyn.com.</p>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
    <p style="font-size: 12px; color: #94a3b8; margin-bottom: 0;">Regards,<br><strong>TERRAVYN Smart Agriculture</strong></p>
  </div>
</body>
</html>"""

    return _dispatch_email(customer_email, subject, body, html_body)

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

