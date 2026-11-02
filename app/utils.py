"""
Utility functions for Mess Management System
Includes QR code generation, PDF generation, and email notifications
"""

import qrcode
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app
from flask_mail import Mail, Message
from datetime import datetime

# Initialize Flask-Mail (will be configured in __init__.py)
mail = Mail()


def generate_qr_code(data, size=10, border=2):
    """
    Generate QR code and return as base64 encoded image
    
    Args:
        data (str): Data to encode in QR code
        size (int): Size of QR code (default: 10)
        border (int): Border thickness (default: 2)
    
    Returns:
        str: Base64 encoded PNG image
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    
    # Add data
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def generate_booking_qr(booking_token, booking_info):
    """
    Generate QR code specifically for meal booking
    
    Args:
        booking_token (str): Unique booking token
        booking_info (dict): Additional booking information
    
    Returns:
        str: Base64 encoded QR code image
    """
    # Create QR data with booking details
    qr_data = f"MESS_BOOKING:{booking_token}"
    
    return generate_qr_code(qr_data, size=8, border=1)


def generate_daily_report_pdf(stats, report_date):
    """
    Generate PDF for daily meal report
    
    Args:
        stats (dict): Report statistics
        report_date (str): Date of the report
    
    Returns:
        BytesIO: PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12
    )
    
    # Title
    title = Paragraph("Mess Management System", title_style)
    subtitle = Paragraph(f"Daily Report - {stats['date'].strftime('%B %d, %Y')}", styles['Heading2'])
    elements.append(title)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    summary_heading = Paragraph("Summary", heading_style)
    elements.append(summary_heading)
    
    summary_data = [
        ['Metric', 'Count'],
        ['Total Bookings', str(stats['total_bookings'])],
        ['Consumed', str(stats['consumed'])],
        ['Pending', str(stats['pending'])],
        ['Cancelled', str(stats['cancelled'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Meal breakdown
    meal_heading = Paragraph("Meal Breakdown", heading_style)
    elements.append(meal_heading)
    
    meal_data = [
        ['Meal Type', 'Bookings'],
        ['Breakfast', str(stats['breakfast'])],
        ['Lunch', str(stats['lunch'])],
        ['Dinner', str(stats['dinner'])]
    ]
    
    meal_table = Table(meal_data, colWidths=[3*inch, 2*inch])
    meal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(meal_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_monthly_report_pdf(stats, report_date):
    """
    Generate PDF for monthly meal report
    
    Args:
        stats (dict): Report statistics
        report_date (str): Month and year of report
    
    Returns:
        BytesIO: PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12
    )
    
    # Title
    title = Paragraph("Mess Management System", title_style)
    subtitle = Paragraph(f"Monthly Report - {stats['month']}", styles['Heading2'])
    elements.append(title)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary section
    summary_heading = Paragraph("Monthly Summary", heading_style)
    elements.append(summary_heading)
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Bookings', str(stats['total_bookings'])],
        ['Total Revenue', f"₹{stats['total_revenue']:.2f}"],
        ['Active Students', str(stats['total_students'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_email(to, subject, template, **kwargs):
    """
    Send email notification
    
    Args:
        to (str or list): Recipient email address(es)
        subject (str): Email subject
        template (str): Email template name
        **kwargs: Template variables
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
        )
        
        # Render email template
        msg.html = render_email_template(template, **kwargs)
        
        # Send email
        mail.send(msg)
        return True
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Email sending failed: {str(e)}")
        return False


def render_email_template(template_name, **kwargs):
    """
    Render email template with variables
    
    Args:
        template_name (str): Template identifier
        **kwargs: Template variables
    
    Returns:
        str: Rendered HTML email
    """
    # Email templates
    templates = {
        'booking_confirmation': """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #2c3e50;">Meal Booking Confirmation</h2>
                <p>Dear {student_name},</p>
                <p>Your meal has been booked successfully!</p>
                <div style="background-color: #ecf0f1; padding: 15px; margin: 20px 0;">
                    <p><strong>Booking Details:</strong></p>
                    <ul>
                        <li>Date: {booking_date}</li>
                        <li>Meal Type: {meal_type}</li>
                        <li>Token: {token}</li>
                        <li>Price: ₹{price}</li>
                    </ul>
                </div>
                <p>Please show this token to staff during meal verification.</p>
                <p>Thank you,<br>Mess Management Team</p>
            </body>
            </html>
        """,
        
        'booking_cancelled': """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #e74c3c;">Meal Booking Cancelled</h2>
                <p>Dear {student_name},</p>
                <p>Your meal booking has been cancelled.</p>
                <div style="background-color: #ecf0f1; padding: 15px; margin: 20px 0;">
                    <p><strong>Cancelled Booking:</strong></p>
                    <ul>
                        <li>Date: {booking_date}</li>
                        <li>Meal Type: {meal_type}</li>
                    </ul>
                </div>
                <p>If you did not request this cancellation, please contact the admin immediately.</p>
                <p>Thank you,<br>Mess Management Team</p>
            </body>
            </html>
        """,
        
        'payment_confirmation': """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #27ae60;">Payment Received</h2>
                <p>Dear {student_name},</p>
                <p>We have received your payment.</p>
                <div style="background-color: #ecf0f1; padding: 15px; margin: 20px 0;">
                    <p><strong>Payment Details:</strong></p>
                    <ul>
                        <li>Amount: ₹{amount}</li>
                        <li>Transaction ID: {transaction_id}</li>
                        <li>Date: {payment_date}</li>
                        <li>Month: {month}</li>
                    </ul>
                </div>
                <p>Thank you for your payment!</p>
                <p>Best regards,<br>Mess Management Team</p>
            </body>
            </html>
        """,
        
        'low_stock_alert': """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #e67e22;">Low Stock Alert</h2>
                <p>Dear Admin,</p>
                <p>The following inventory items are running low:</p>
                <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <ul>
                        {items_list}
                    </ul>
                </div>
                <p>Please restock these items as soon as possible.</p>
                <p>System Alert,<br>Mess Management System</p>
            </body>
            </html>
        """
    }
    
    # Get template and format with kwargs
    template = templates.get(template_name, "")
    return template.format(**kwargs)
