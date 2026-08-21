import os
from twilio.rest import Client


def send_whatsapp_receipt(student_mobile, pdf_url, student_name, amount, status):
    # Render Environment Variables मधून Credentials वाचणे
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number = "whatsapp:+17372508034"

    if not account_sid or not auth_token:
        print("Error: Twilio Credentials Environment Variables मध्ये सापडले नाहीत.")
        return False

    try:
        client = Client(account_sid, auth_token)

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
            from_=twilio_whatsapp_number,
            body=message_body,
            media_url=[pdf_url],
            to=formatted_mobile,
        )

        print(f"WhatsApp Message Sent Successfully! SID: {message.sid}")
        return True

    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False
