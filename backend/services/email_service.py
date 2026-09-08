import smtplib
from email.message import EmailMessage
import logging
from database.connection import settings
import os

logger = logging.getLogger("uvicorn.error")

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
        strategies = [(True, 465), (False, 587)]
    else:
        strategies = [(False, configured_port), (True, 465)]

    last_error = None
    for use_ssl, try_port in strategies:
        try:
            logger.info(f"[SMTP ATTEMPT] Connecting to {host}:{try_port} (SSL={use_ssl}) for {recipient_email}...")
            if use_ssl:
                server = smtplib.SMTP_SSL(host, try_port, timeout=15)
            else:
                server = smtplib.SMTP(host, try_port, timeout=15)
                server.ehlo()
                if settings.SMTP_USE_TLS or try_port == 587:
                    server.starttls()
                    server.ehlo()
            
            with server:
                server.login(username, password)
                server.send_message(msg)
            
            logger.info(f"[SMTP SUCCESS] Email successfully delivered to {recipient_email} via {host}:{try_port}")
            return True
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error(f"[SMTP AUTH FAILED] Authentication failed for user '{username}' on {host}:{try_port}. Error: {str(auth_err)}")
            last_error = auth_err
            # Break if authentication specifically fails (e.g. wrong app password)
            break
        except Exception as e:
            logger.warning(f"[SMTP STRATEGY FAILED] Connection to {host}:{try_port} failed: {str(e)}")
            last_error = e

    logger.error(f"[SMTP DELIVERY FAILED] Could not send email to {recipient_email}. Last error: {str(last_error)}")
    return False

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
    return _send_smtp_message(msg, recipient_email)

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
    return _send_smtp_message(msg, recipient_email)

