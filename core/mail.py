from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives


from django.template.loader import render_to_string
from django.utils.html import strip_tags

def _send_email(
    recipient, subject="", body_text="", body_html="", attachments=None, quiet=True
):
    """
    Sends email to recipient.
    """
    from django.contrib.staticfiles import finders
    _logos = [finders.find("images/logo.png")]

    body_html = body_html or f"<p>{body_text}</p>"

    email = EmailMultiAlternatives(
        subject=subject,
        body=f"{body_text}\n",
        from_email=settings.EMAIL_FROM,
        to=[recipient],
        alternatives=[(body_html, "text/html")],
        attachments=attachments,
    )

    # always attach logos
    for img_path in _logos:
        if img_path:
            img_name = img_path.split("/")[-1]

            with open(img_path, "rb") as fp:
                img_file = MIMEImage(fp.read())

            img_file.add_header("Content-ID", f"<{img_name}>")

            email.attach(img_file)

    email.send(fail_silently=quiet)
    return email


def send_email(enqueue=False, *args, **kwargs):
    if settings.REDIS_ENABLED and enqueue:
        from django_rq import get_queue

        queue = get_queue(settings.RQ_SENDER_QUEUE)
        queue.enqueue(_send_email, *args, **kwargs)

    else:
        _send_email(*args, **kwargs)


def send_templated_email(recipient, subject, template_name, context, enqueue=False, attachments=None):
    """
    Renders an HTML template and sends it.
    """
    html_content = render_to_string(f"emails/{template_name}", context)
    text_content = strip_tags(html_content)
    
    send_email(
        enqueue=enqueue,
        recipient=recipient,
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        attachments=attachments
    )

def send_receipt_email(blood_request):
    """
    Generates a receipt PDF and sends it to the requester.
    """
    from core.utils.pdf import generate_receipt_pdf
    pdf_content = generate_receipt_pdf(blood_request)
    
    if not pdf_content:
        return
    
    recipient = blood_request.requester_user.email
    if blood_request.requester_hospital:
        recipient = blood_request.requester_hospital.contact_email or recipient
        
    subject = f"Payment Receipt - SA-{blood_request.id:06d}"
    
    # Attachments format: (filename, content, mimetype)
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
            "service_fee": f"{blood_request.service_fee:,.2f}"
        },
        attachments=attachments
    )
