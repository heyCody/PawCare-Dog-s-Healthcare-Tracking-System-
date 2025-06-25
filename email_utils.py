import smtplib
import ssl
import random
import os
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # Make sure you load your .env file here

class SendEmail:
    def __init__(self, msg_html, mail_to, subject="Your OTP Code"):
        self.msg_html = msg_html
        self.mail_to = mail_to
        self.subject = subject

    def email_main_send(self):
        smtp_port = int(os.environ.get("MAIL_PORT", 587))
        smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        email_from = os.environ.get("MAIL_USERNAME")
        email_to = self.mail_to
        pswd = os.environ.get("MAIL_PASSWORD")

        # Validate required environment variables
        if not email_from or not pswd:
            print("❌ Missing email credentials in environment variables")
            return False

        message = MIMEMultipart("alternative")
        message["From"] = email_from
        message["To"] = email_to
        message["Subject"] = self.subject
        part_html = MIMEText(self.msg_html, "html", "utf-8")
        message.attach(part_html)

        simple_email_context = ssl.create_default_context()
        server = None
        try:
            print("📨 Connecting to SMTP server...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls(context=simple_email_context)
            server.login(email_from, pswd)
            # Fixed: Properly encode the message to handle Unicode characters (emojis)
            message_string = message.as_string()
            server.sendmail(email_from, email_to, message_string.encode('utf-8'))
            print(f"✅ OTP Email sent to - {email_to}")
            return True
        except Exception as e:
            print(f"❌ Error sending OTP email: {e}")
            traceback.print_exc()
            return False
        finally:
            if server:
                server.quit()

def generate_otp():
    return random.randint(100000, 999999)

def build_otp_email(code):
    return f"""
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h2 style="color: white; margin: 0; font-size: 24px;">Your OTP Code 🐾</h2>
          </div>
          <div style="padding: 30px;">
            <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
              Thank you for choosing PawCare 🐾!
            </p>
            <p style="color: #333; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
              Your OTP for verification is:
            </p>
            <div style="text-align: center; margin: 30px 0;">
              <div style="display: inline-block; background-color: #f8f9fa; border: 2px dashed #0b79d0; border-radius: 8px; padding: 20px;">
                <h1 style="color: #0b79d0; margin: 0; font-size: 36px; font-weight: bold; letter-spacing: 3px;">{code}</h1>
              </div>
            </div>
            <p style="color: #666; font-size: 14px; text-align: center; margin: 30px 0;">
              This OTP is valid for <strong>10 minutes</strong> only.
            </p>
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
              <p style="color: #856404; margin: 0; font-size: 14px;">
                <strong>Security Note:</strong> Never share this OTP with anyone. PawCare will never ask for your OTP via phone or email.
              </p>
            </div>
          </div>
          <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="font-size: 12px; color: #6c757d; margin: 0;">
              &copy; 2025 PawCare 🐾 | Contact: pawcare@gmail.com
            </p>
          </div>
        </div>
      </body>
    </html>
    """