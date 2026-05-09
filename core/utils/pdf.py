import os
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def generate_receipt_pdf(blood_request):
    """
    Generates a receipt PDF for a given blood request.
    """
    from django.contrib.staticfiles import finders
    import base64
    import mimetypes
    
    logo_path = finders.find("images/logo.png")
    logo_data = None
    if logo_path:
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(logo_path)
            logo_data = f"data:{mime_type};base64,{encoded_string}"
    
    # context data
    context = {
        "logo_data": logo_data,
        "reference": f"REF-{blood_request.id:06d}",
        "date": blood_request.date_created,
        "requester_name": blood_request.requester_hospital.name if blood_request.requester_hospital else f"{blood_request.requester_user.first_name} {blood_request.requester_user.last_name}",
        "requester_address": blood_request.requester_hospital.address if blood_request.requester_hospital else "",
        "requester_email": blood_request.requester_hospital.contact_email if blood_request.requester_hospital else blood_request.requester_user.email,
        
        "product_name": blood_request.product.category.name if blood_request.product and blood_request.product.category else "Whole Blood",
        "blood_group": blood_request.product.blood_group if blood_request.product else "N/A",
        "quantity": blood_request.quantity,
        "unit_price": float(blood_request.blood_price) / blood_request.quantity if blood_request.quantity > 0 else 0,
        "blood_price": float(blood_request.blood_price),
        "service_fee": float(blood_request.service_fee),
        "delivery_fee": float(blood_request.delivery_fee),
        "commission_amount": float(blood_request.commission_amount),
        "total_amount": float(blood_request.total_amount),
        
        "swift_aid_address": getattr(config, 'address', "123 SwiftAid Tech Plaza, Lagos, Nigeria"),
        "swift_aid_email": getattr(config, 'contact_email', "support@swiftaid.com"),
        "swift_aid_phone": getattr(config, 'contact_phone', "+234 800 SWIFTAID"),
    }
    
    # If it's a POS sale or has a blood bank, add facility details
    if blood_request.source == 'POS' or blood_request.blood_bank:
        bb = blood_request.blood_bank
        if bb:
            context.update({
                "facility_name": bb.name,
                "facility_address": bb.address,
                "facility_phone": bb.contact_phone,
                "facility_email": bb.contact_email,
            })
            
    return render_to_pdf('receipts/receipt.html', context)
