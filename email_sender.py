import smtplib
from email.message import EmailMessage
import urllib.parse

# ==================================
# GMAIL SETTINGS
# ==================================
EMAIL_ADDRESS = "birthdaysceduler@gmail.com"
EMAIL_PASSWORD = "fjtt ahqy tihf jjrk"


# ==================================
# SEND EMAIL FUNCTION
# ==================================
def send_email(subject, body):

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

            smtp.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            smtp.send_message(msg)

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email failed")
        print(e)


# ==================================
# TEST
# ==================================
if __name__ == "__main__":

    send_email(
        "Birthday Scheduler Test",
        "If you received this email, Gmail integration is working."
    )