import os
from twilio.rest import Client

# Twilio Credentials (तुमच्या Twilio Dashboard वरून मिळतील)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid_here")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio Sandbox Number


def send_whatsapp_receipt(student_mobile, pdf_url, student_name, amount, status):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # भारतीय मोबाईल नंबरसाठी +91 फॉर्मेट
        formatted_mobile = f"whatsapp:+91{student_mobile.strip()}"

        message_body = (
            f"Hello {student_name},\n\n"
            f"Your Hostel Fee status has been updated.\n"
            f"Status: *{status}*\n"
            f"Amount: *Rs. {amount}*\n\n"
            f"Please find your official fee receipt attached below."
        )

        message = client.messages.create(
            media_url=[pdf_url],
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=formatted_mobile,
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False