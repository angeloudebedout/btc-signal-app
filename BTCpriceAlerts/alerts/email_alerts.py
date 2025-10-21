# alerts/email_alerts.py

import smtplib
from email.message import EmailMessage

def send_alert(subject, body, to_email):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = "youremail@gmail.com"
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("youremail@gmail.com", "your-app-password")
            smtp.send_message(msg)
            print("✅ Alert sent to", to_email)
    except Exception as e:
        print("❌ Failed to send email:", e)
