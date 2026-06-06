from flask import Flask, render_template, request, redirect, Response
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime, date
import csv
import urllib.parse

from scheduler import (
    check_birthdays,
    get_todays_birthdays
)

from twilio.rest import Client

# ==============================
# Flask app
# ==============================
app = Flask(__name__)

# ==============================
# Twilio setup
# ==============================
TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# ==============================
# SEND WHATSAPP MESSAGE
# ==============================
def send_whatsapp_message(phone, message):
    try:
        clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "").strip()

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=f"whatsapp:+{clean_phone}"
        )

        print(f"[SENT] {phone}")

    except Exception as e:
        print(f"[ERROR] {phone}: {e}")

# ==============================
# SEND BIRTHDAY MESSAGES
# ==============================
def send_birthday_messages():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name, phone, message, birthday FROM birthdays")
    rows = cursor.fetchall()
    conn.close()

    today = date.today()

    for row in rows:
        birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

        if birthday_date.month == today.month and birthday_date.day == today.day:

            name = row[0]
            phone = row[1]
            message = row[2]

            final_message = message.replace("{name}", name)

            send_whatsapp_message(phone, final_message)

# ==============================
# HOME PAGE
# ==============================
@app.route('/')
def home():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, message
        FROM birthdays
    """)
    rows = cursor.fetchall()
    conn.close()

    today = date.today()
    upcoming = []

    total_birthdays = len(rows)
    birthdays_today_count = 0
    birthdays_this_month = 0

    for row in rows:

        birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

        if birthday_date.month == today.month:
            birthdays_this_month += 1

        if birthday_date.month == today.month and birthday_date.day == today.day:
            birthdays_today_count += 1

        next_birthday = date(today.year, birthday_date.month, birthday_date.day)

        if next_birthday < today:
            next_birthday = date(today.year + 1, birthday_date.month, birthday_date.day)

        days_until = (next_birthday - today).days

        birth_year = birthday_date.year
        current_age = today.year - birth_year

        if (
            today.month < birthday_date.month or
            (today.month == birthday_date.month and today.day < birthday_date.day)
        ):
            current_age -= 1

        turning_age = current_age + 1

        message_text = row[4].replace("{name}", row[1])
        phone = row[2].replace("+", "").strip()

        whatsapp_link = (
            "https://wa.me/" + phone +
            "?text=" + urllib.parse.quote(message_text)
        )

        upcoming.append({
            "id": row[0],
            "name": row[1],
            "phone": phone,
            "birthday": row[3],
            "message": message_text,
            "days": days_until,   # ✅ FIXED
            "age": current_age,
            "turning_age": turning_age,
            "whatsapp_link": whatsapp_link
        })

    upcoming.sort(key=lambda x: x["days"])

    if upcoming:
        next_birthday_name = upcoming[0]["name"]
        next_birthday_days = upcoming[0]["days"]
    else:
        next_birthday_name = "None"
        next_birthday_days = 0

    return render_template(
        "index.html",
        upcoming=upcoming,
        total_birthdays=total_birthdays,
        birthdays_today_count=birthdays_today_count,
        birthdays_this_month=birthdays_this_month,
        next_birthday_name=next_birthday_name,
        next_birthday_days=next_birthday_days
    )

# ==============================
# UPCOMING PAGE (FIXED)
# ==============================
@app.route('/upcoming')
def upcoming_birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, message
        FROM birthdays
    """)
    rows = cursor.fetchall()
    conn.close()

    today = date.today()
    upcoming = []

    for row in rows:

        birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

        # next birthday calculation
        next_birthday = date(today.year, birthday_date.month, birthday_date.day)

        if next_birthday < today:
            next_birthday = date(today.year + 1, birthday_date.month, birthday_date.day)

        days_until = (next_birthday - today).days

        if days_until <= 30:

            name = row[1]
            phone = row[2].replace("+", "").replace(" ", "").strip()
            message = row[4]

            # replace name placeholder
            message_text = message.replace("{name}", name)

            whatsapp_link = (
                "https://wa.me/" +
                phone +
                "?text=" +
                urllib.parse.quote(message_text)
            )

            upcoming.append({
                "id": row[0],
                "name": name,
                "birthday": row[3],
                "days": days_until,   # ✅ REQUIRED FOR TEMPLATE
                "phone": phone,
                "message": message_text,
                "whatsapp_link": whatsapp_link
            })

    upcoming.sort(key=lambda x: x["days"])

    return render_template("upcoming.html", upcoming=upcoming)
# ==============================
# ADD BIRTHDAY
# ==============================
@app.route('/add', methods=['GET', 'POST'])
def add_birthday():

    if request.method == 'POST':

        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        birthday = request.form['birthday'].strip()
        message = request.form['message'].strip()

        conn = sqlite3.connect('birthdays.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM birthdays WHERE phone=?", (phone,))
        if cursor.fetchone():
            return "Duplicate phone"

        cursor.execute("""
            INSERT INTO birthdays (name, phone, birthday, message)
            VALUES (?, ?, ?, ?)
        """, (name, phone, birthday, message))

        conn.commit()
        conn.close()

        return redirect('/birthdays')

    return render_template('add_birthday.html')

# ==============================
# VIEW ALL
# ==============================
@app.route('/birthdays')
def birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM birthdays")
    rows = cursor.fetchall()

    conn.close()

    return render_template('birthdays.html', birthdays=rows)

# ==============================
# DELETE
# ==============================
@app.route('/delete/<int:id>')
def delete_birthday(id):

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM birthdays WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/birthdays')

# ==============================
# SEND NOW
# ==============================
@app.route('/send-now')
def send_now():

    try:
        send_birthday_messages()
        return "<h2>✅ Messages Sent Successfully!</h2><a href='/'>Back</a>"
    except Exception as e:
        return f"<h2>❌ Error: {e}</h2>"

# ==============================
# REMINDERS
# ==============================
@app.route('/reminders')
def reminders():
    return render_template('reminders.html', birthdays=get_todays_birthdays())

# ==============================
# SCHEDULER
# ==============================
scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_birthdays, 'interval', minutes=1)
        scheduler.add_job(send_birthday_messages, 'cron', hour=9, minute=0)
        scheduler.start()
        print("[SCHEDULER] Running")


@app.route('/routes')
def routes():
    return "<br>".join(str(r) for r in app.url_map.iter_rules())

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_birthday(id):

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        name = request.form['name']
        phone = request.form['phone']
        birthday = request.form['birthday']
        message = request.form['message']

        cursor.execute("""
            UPDATE birthdays
            SET name=?, phone=?, birthday=?, message=?
            WHERE id=?
        """, (name, phone, birthday, message, id))

        conn.commit()
        conn.close()

        return redirect('/birthdays')

    cursor.execute("SELECT * FROM birthdays WHERE id=?", (id,))
    birthday = cursor.fetchone()

    conn.close()

    if birthday is None:
        return "Birthday not found"

    return render_template('edit_birthday.html', birthday=birthday)


# ==============================
# SEND SINGLE MESSAGE NOW
# ==============================
@app.route('/send/<int:id>')
def send_single_message(id):

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, phone, message
        FROM birthdays
        WHERE id=?
    """, (id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return "Birthday not found"

    name = row[0]
    phone = row[1]
    message = row[2]

    final_message = message.replace("{name}", name)

    send_whatsapp_message(phone, final_message)

    return redirect('/birthdays')

@app.route('/import', methods=['GET', 'POST'])
def import_birthdays():

    if request.method == 'POST':

        file = request.files['file']

        if file:

            decoded = file.read().decode('utf-8')
            reader = csv.DictReader(decoded.splitlines())

            conn = sqlite3.connect('birthdays.db')
            cursor = conn.cursor()

            for row in reader:

                name = row.get('Name', '').strip()
                phone = row.get('Phone', '').strip()
                birthday = row.get('Birthday', '').strip()
                message = row.get('Message', '').strip()

                if not name or not phone:
                    continue

                cursor.execute("""
                    INSERT INTO birthdays
                    (name, phone, birthday, message)
                    VALUES (?, ?, ?, ?)
                """, (
                    name,
                    phone,
                    birthday,
                    message
                ))

            conn.commit()
            conn.close()

            return redirect('/birthdays')

    return render_template('import.html')

@app.route('/search')
def search():

    query = request.args.get('q', '').strip()

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM birthdays
        WHERE name LIKE ?
        OR phone LIKE ?
    """, (f'%{query}%', f'%{query}%'))

    results = cursor.fetchall()

    conn.close()

    return render_template(
        'birthdays.html',
        birthdays=results
    )
# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, use_reloader=False)