import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

# Admin credentials
ADMIN_EMAIL = "santhosh6382572352@gmail.com"
ADMIN_APP_PASSWORD = "ipao nqap fgyp zkeu"

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_admin_notification(user_data, otp):
    """Send notification to admin with user registration details and OTP"""
    sender_email = ADMIN_EMAIL
    sender_password = ADMIN_APP_PASSWORD
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ADMIN_EMAIL
    message["Subject"] = f"New {user_data['role'].title()} Registration Request"
    
    # Email body
    body = f"""
    New registration request:
    
    Name: {user_data['name']}
    Email: {user_data['email']}
    Role: {user_data['role']}
    
    OTP for verification: {otp}
    """
    
    message.attach(MIMEText(body, "plain"))
    
    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_otp_to_user(email, otp):
    """Send OTP to user's email"""
    sender_email = ADMIN_EMAIL
    sender_password = ADMIN_APP_PASSWORD
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "OTP for Healthcare Monitoring System Registration"
    
    # Email body
    body = f"""
    Your OTP for registration verification is: {otp}
    
    Please enter this OTP to complete your registration.
    If you didn't request this, please ignore this email.
    """
    
    message.attach(MIMEText(body, "plain"))
    
    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False 