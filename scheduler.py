from email_sender import send_email
import sqlite3
from datetime import date, datetime


# ==============================
# GET TODAY'S BIRTHDAYS
# ==============================
def get_todays_birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM birthdays")
    rows = cursor.fetchall()

    conn.close()

    today = date.today()
    birthdays_today = []

    for row in rows:

        try:
            birthdate_str = row[3]
            birthday_date = datetime.strptime(
                birthdate_str,
                "%Y-%m-%d"
            ).date()

        except (ValueError, IndexError, TypeError):
            continue

        if (
            birthday_date.month == today.month
            and birthday_date.day == today.day
        ):
            birthdays_today.append(row)

    return birthdays_today


# ==============================
# MESSAGE RENDERER (SAFE)
# ==============================
def render_message(template, context):

    try:
        return template.format(**context)

    except KeyError as e:
        print(f"[Template Warning] Missing key: {e}")
        return template

    except Exception as e:
        print(f"[Template Error] {e}")
        return template


# ==============================
# WHATSAPP SENDER (PLACEHOLDER)
# ==============================
def send_whatsapp_message(phone, message):

    print(
        f"[WHATSAPP] Sending to {phone}: {message}"
    )


# ==============================
# MAIN CHECK FUNCTION
# ==============================
def check_birthdays():

    birthdays_today = get_todays_birthdays()

    print("\n[Scheduler] Checking birthdays...")

    if not birthdays_today:
        print("[Scheduler] No birthdays today.")
        return

    print("\n[Scheduler] Sending messages...\n")

    for birthday in birthdays_today:

        try:
            name = birthday[1]
            phone = birthday[2]

        except IndexError:
            continue

        try:
            message_template = birthday[4]

            if not message_template:
                raise ValueError

        except:
            message_template = (
                "Happy Birthday {name}! ❤️"
            )

        context = {
            "name": name,
            "phone": phone
        }

        message = render_message(
            message_template,
            context
        )

        print(
            f"Sending to {name} ({phone})"
        )

        send_whatsapp_message(
            phone,
            message
        )

        email_body = f"""
Today is {name}'s birthday!

Phone:
{phone}

Suggested Message:
{message}
"""

        send_email(
            f"Birthday Reminder - {name}",
            email_body
        )

        print(
            f"Email reminder sent for {name}"
        )


# ==============================
# RUN ONCE (TEST MODE)
# ==============================
if __name__ == "__main__":

    check_birthdays()