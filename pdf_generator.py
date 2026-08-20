import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_fee_receipt(fee, student):
    # Absolute Path वापरून फोल्डर खात्रीने तयार करणे
    base_dir = os.path.abspath(os.path.dirname(__file__))
    receipts_dir = os.path.join(base_dir, "static", "receipts")
    os.makedirs(receipts_dir, exist_ok=True)

    # PDF फाईलचा पूर्ण Absolute Path
    file_path = os.path.join(receipts_dir, f"receipt_{fee.id}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,
        spaceAfter=15
    )

    elements.append(Paragraph("<b>HOSTEL FEE RECEIPT</b>", title_style))
    elements.append(Spacer(1, 15))

    current_datetime = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    data = [
        ["Receipt Date & Time:", current_datetime],
        ["Student Name:", student.name],
        ["Room Number:", f"Room {student.room_no}"],
        ["Mobile Number:", student.mobile_no],
        ["Duration:", fee.duration],
        ["Amount Paid/Due:", f"Rs. {fee.amount}"],
        ["Payment Status:", fee.status]
    ]

    t = Table(data, colWidths=[180, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#dcdde1')),
    ]))

    elements.append(t)
    elements.append(Spacer(1, 30))

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=1
    )
    elements.append(Paragraph("Thank you! This is a computer-generated receipt.", footer_style))

    doc.build(elements)
    return file_path