import os
from twilio.rest import Client

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid_here")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token_here")
# 'whatsapp:' प्रीफिक्स जोडणे अत्यंत आवश्यक आहे
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"


def send_whatsapp_receipt(student_mobile, pdf_url, student_name, amount, status):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # मोबाईल नंबरमधील मोकळी जागा काढून +91 फॉरमॅट करणे
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
