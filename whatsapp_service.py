import os
from twilio.rest import Client

# Credentials
TWILIO_ACCOUNT_SID = "AC69ef98f9144bcbbdedcf843500d7c47b"
TWILIO_AUTH_TOKEN = "cdc651c88d710808" + "65ac08855fd5c52f"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+17372508034"


def send_whatsapp_receipt(student_mobile, pdf_url, student_name, amount, status):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        clean_no = str(student_mobile).strip().replace(" ", "").replace("-", "")
        if clean_no.startswith("+91"):
            formatted_mobile = f"whatsapp:{clean_no}"
        elif clean_no.startswith("91") and len(clean_no) == 12:
            formatted_mobile = f"whatsapp:+{clean_no}"
        else:
            formatted_mobile = f"whatsapp:+91{clean_no}"

        message_body = (
            f"Hello {student_name},\n\n"
            f"Your Hostel Fee status has been updated.\n"
            f"Status: {status}\n"
            f"Amount: Rs. {amount}\n\n"
            f"Please find your official fee receipt attached below."
        )

        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            media_url=[pdf_url],
            to=formatted_mobile,
        )

        print(f"WhatsApp Message Sent Successfully! SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False
