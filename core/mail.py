import logging
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_email(recipient, subject="", body_text="", body_html="", attachments=None, quiet=True):
    """
    Sends an email via Django's SMTP backend.
    `attachments` is a list of (filename, content_bytes, mimetype) tuples.
    """
    body_html = body_html or f"<p>{body_text}</p>"

    # Use EMAIL_FROM if set in settings, fallback to standard Django DEFAULT_FROM_EMAIL
    from_email = getattr(settings, "EMAIL_FROM", getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@swiftaid.coo"))

    email = EmailMultiAlternatives(
        subject=subject,
        body=f"{body_text}\n",
        from_email=from_email,
        to=[recipient],
        alternatives=[(body_html, "text/html")],
    )

    if attachments:
        for filename, content, mimetype in attachments:
            email.attach(filename, content, mimetype)

    try:
        email.send(fail_silently=quiet)
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP to {recipient}: {e}")
        if not quiet:
            raise
        return False


def send_email(enqueue=False, *args, **kwargs):
    if settings.REDIS_ENABLED and enqueue:
        from django_rq import get_queue
        queue = get_queue(settings.RQ_SENDER_QUEUE)
        queue.enqueue(_send_email, *args, **kwargs)
    else:
        _send_email(*args, **kwargs)


def send_templated_email(recipient, subject, template_name, context, enqueue=False, attachments=None):
    """
    Renders an HTML template and sends it via SMTP.
    """
    try:
        html_content = render_to_string(f"emails/{template_name}", context)
        text_content = strip_tags(html_content)

        send_email(
            enqueue=enqueue,
            recipient=recipient,
            subject=subject,
            body_text=text_content,
            body_html=html_content,
            attachments=attachments,
        )
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        raise


# ---------------------------------------------------------------------------
# User account emails
# ---------------------------------------------------------------------------

def send_verification_email(user_email, otp_code):
    """
    Sends an OTP verification email to a newly registered user.
    """
    send_templated_email(
        recipient=user_email,
        subject="Verify Your SwiftAid Account",
        template_name="verification_email.html",
        context={
            "email": user_email,
            "otp_code": otp_code,
            "expiry_minutes": settings.OTP_EXPIRY_MINUTES,
        },
    )


def send_onboarding_email(user_email, temporary_password, facility_name, facility_type, portal_url, inviter_name=None, role=None):
    """
    Sends an onboarding email for hospital, blood bank, staff, or internal admin users
    who are invited by an existing user.
    `facility_type` should be one of: 'hospital', 'blood_bank', 'admin'
    `role` should be a human-readable string e.g. 'ADMIN' or 'STAFF'
    """
    send_templated_email(
        recipient=user_email,
        subject=f"You've Been Invited to SwiftAid — {facility_name}",
        template_name="new_user.html",
        context={
            "email": user_email,
            "temporary_password": temporary_password,
            "facility_name": facility_name,
            "facility_type": facility_type,
            "portal_url": portal_url,
            "inviter_name": inviter_name,
            "role": role,
        },
    )


def send_password_reset_email(user_email, reset_code):
    """
    Sends a password reset OTP email.
    """
    send_templated_email(
        recipient=user_email,
        subject="Password Reset Request — SwiftAid",
        template_name="forgot_password.html",
        context={
            "email": user_email,
            "reset_code": reset_code,
        },
    )


def send_password_changed_email(user_email):
    """
    Sends a confirmation email after a successful password change.
    """
    send_templated_email(
        recipient=user_email,
        subject="Your Password Has Been Changed — SwiftAid",
        template_name="password_changed.html",
        context={
            "email": user_email,
            "support_url": settings.FRONTEND_BASE_URL,
        },
    )


# ---------------------------------------------------------------------------
# Transactional emails
# ---------------------------------------------------------------------------

def send_receipt_email(blood_request):
    """
    Generates a receipt PDF and sends it to the requester.
    """
    try:
        from core.utils.pdf import generate_receipt_pdf
        pdf_content = generate_receipt_pdf(blood_request)

        if not pdf_content:
            return

        recipient = blood_request.requester_user.email
        if blood_request.requester_hospital:
            recipient = blood_request.requester_hospital.contact_email or recipient

        subject = f"Payment Receipt - SA-{blood_request.id:06d}"
        attachments = [(f"Receipt-SA-{blood_request.id:06d}.pdf", pdf_content, "application/pdf")]

        send_templated_email(
            recipient=recipient,
            subject=subject,
            template_name="receipt_notification.html",
            context={
                "reference": f"REF-{blood_request.id:06d}",
                "amount": f"{blood_request.total_amount:,.2f}",
                "blood_group": blood_request.product.blood_group if blood_request.product else "N/A",
                "quantity": blood_request.quantity,
                "blood_price": f"{blood_request.blood_price:,.2f}",
                "service_fee": f"{blood_request.service_fee:,.2f}",
            },
            attachments=attachments,
        )
    except Exception as e:
        logger.error(f"Failed to generate/send receipt for BloodRequest {blood_request.id}: {e}")
