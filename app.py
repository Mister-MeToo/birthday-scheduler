import os
from dotenv import load_dotenv
from flask import jsonify
from flask import Flask, render_template, request, redirect, Response, flash, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from datetime import datetime, date
import csv
import urllib.parse
from werkzeug.utils import secure_filename

from scheduler import (
    check_birthdays,
    get_todays_birthdays
)

from twilio.rest import Client

load_dotenv()
# ==============================
# Flask app
# ==============================
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
serializer = URLSafeTimedSerializer(app.secret_key)
# ==============================
# Twilio setup
# ==============================
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# ==============================
# Email setup
# ==============================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not all([
    os.getenv("SECRET_KEY"),
    os.getenv("TWILIO_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
    os.getenv("EMAIL_ADDRESS"),
    os.getenv("EMAIL_PASSWORD")
]):
    raise Exception("Missing environment variables.")

# ==============================
# Upload Photos
# ==============================
UPLOAD_FOLDER = 'static/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
# SEND EMAIL
# ==============================
def send_email(to_email, name, message):
    try:
        msg = MIMEMultipart("alternative")

        msg["Subject"] = f"🎂 Happy Birthday {name}!"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:30px;">
            <div style="
                max-width:500px;
                margin:auto;
                background:white;
                padding:30px;
                border-radius:16px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);
                text-align:center;
            ">
                <div style="font-size:60px;">🎂</div>

                <h1 style="color:#2c3e50;">
                    Happy Birthday, {name}!
                </h1>

                <p style="
                    font-size:16px;
                    color:#555;
                    line-height:1.6;
                ">
                    {message}
                </p>

                <div style="
                    margin-top:20px;
                    padding:15px;
                    background:#f9f9f9;
                    border-radius:8px;
                ">
                    <p style="color:#888;font-size:13px;">
                        Sent with ❤️ from Birthday Scheduler
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_ADDRESS,
                to_email,
                msg.as_string()
            )

        print(f"[EMAIL SENT] {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] {to_email}: {e}")
        return False

def send_verification_email(email):

    def send_reset_email(email, reset_url):

        msg = MIMEMultipart("alternative")

        msg["Subject"] = "Reset Your Password"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:30px;">
            <div style="
                max-width:500px;
                margin:auto;
                background:white;
                padding:30px;
                border-radius:16px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);
            ">

                <h2>Password Reset Request</h2>

                <p>
                    We received a request to reset your password.
                </p>

                <p>
                    Click the button below:
                </p>

                <p>
                    <a href="{reset_url}"
                       style="
                           background:#007bff;
                           color:white;
                           padding:12px 20px;
                           text-decoration:none;
                           border-radius:6px;
                           display:inline-block;
                       ">
                        Reset Password
                    </a>
                </p>

                <p>
                    This link expires in 1 hour.
                </p>

                <p>
                    If you did not request this, ignore this email.
                </p>

            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_ADDRESS,
                email,
                msg.as_string()
            )

        print(f"[RESET EMAIL SENT] {email}")

    token = serializer.dumps(
        email,
        salt="email-confirm"
    )

    verify_url = url_for(
        "verify_email",
        token=token,
        _external=True
    )

    msg = MIMEMultipart("alternative")

    msg["Subject"] = "Verify Your Account"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    html = f"""
    <html>
    <body>
        <h2>Welcome to Birthday Scheduler 🎂</h2>

        <p>Thank you for registering.</p>

        <p>Click the button below to verify your email address:</p>

        <p>
            <a href="{verify_url}"
               style="
                   background:#4CAF50;
                   color:white;
                   padding:12px 20px;
                   text-decoration:none;
                   border-radius:6px;
               ">
                Verify Account
            </a>
        </p>

        <p>If you did not create this account, please ignore this email.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_ADDRESS,
            email,
            msg.as_string()
        )

    print(f"[VERIFY EMAIL SENT] {email}")

#==============================
# User Model
# ==============================

class User(UserMixin):
    def __init__(self, id, email, password, verified):
        self.id = id
        self.email = email
        self.password = password
        self.verified = verified


@login_manager.user_loader
def load_user(user_id):

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,email,password,verified
        FROM users
        WHERE id=?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return User(
            row[0],
            row[1],
            row[2],
            row[3]
        )

    return None
# ==============================
# SEND BIRTHDAY MESSAGES
# ==============================
def send_birthday_messages():


    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, phone, message, birthday, email FROM birthdays")
    rows = cursor.fetchall()

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    for row in rows:
        birthday_date = datetime.strptime(row[4], "%Y-%m-%d").date()

        if birthday_date.month == today.month and birthday_date.day == today.day:

            birthday_id = row[0]
            name = row[1]
            phone = row[2]
            message = row[3]

            # Check if already sent today
            cursor.execute("""
                SELECT id FROM sent_log
                WHERE birthday_id=? AND sent_date=?
            """, (birthday_id, today_str))

            if cursor.fetchone():
                print(f"[SKIP] Already sent today for {name}")
                continue

            final_message = message.replace("{name}", name)

            # Send WhatsApp
            send_whatsapp_message(phone, final_message)

            # Send Email if available
            if row[5]:
                send_email(row[5], name, final_message)

            # Log it
            cursor.execute("""
                INSERT INTO sent_log (birthday_id, sent_date)
                VALUES (?, ?)
            """, (birthday_id, today_str))

            conn.commit()
            print(f"[LOGGED] Sent for {name} on {today_str}")

    conn.close()

# ==============================
# HOME PAGE
# ==============================

@app.route('/api/stats')
@login_required
def api_stats():

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM birthdays"
    )

    total = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "total_birthdays": total
    })

@app.route('/')
@login_required
def home():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, message, photo
        FROM birthdays
    """)
    rows = cursor.fetchall()
    conn.close()

    today = date.today()
    upcoming = []
    monthly_counts = [0] * 12

    total_birthdays = len(rows)
    birthdays_today_count = 0
    birthdays_this_month = 0
    upcoming_this_week = 0
    oldest_person = ""
    oldest_age = 0
    youngest_person = ""
    youngest_age = 999
    ages = []

    for row in rows:

        birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

        monthly_counts[birthday_date.month - 1] += 1

        if birthday_date.month == today.month:
            birthdays_this_month += 1

        if birthday_date.month == today.month and birthday_date.day == today.day:
            birthdays_today_count += 1

        next_birthday = date(today.year, birthday_date.month, birthday_date.day)

        if next_birthday < today:
            next_birthday = date(today.year + 1, birthday_date.month, birthday_date.day)

        days_until = (next_birthday - today).days

        if 1 <= days_until <= 7:
            upcoming_this_week += 1

        birth_year = birthday_date.year
        current_age = today.year - birth_year

        if (
            today.month < birthday_date.month or
            (today.month == birthday_date.month and today.day < birthday_date.day)
        ):
            current_age -= 1

        ages.append(current_age)

        if current_age > oldest_age:
            oldest_age = current_age
            oldest_person = row[1]

        if current_age < youngest_age:
            youngest_age = current_age
            youngest_person = row[1]

        turning_age = current_age + 1

        message_text = row[4].replace("{name}", row[1])
        phone = (
            row[2]
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
            .strip()
        )

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
            "days": days_until,
            "age": current_age,
            "turning_age": turning_age,
            "whatsapp_link": whatsapp_link,
            "photo": row[5] if len(row) > 5 else ""
        })

    upcoming.sort(key=lambda x: x["days"])

    if ages:
        average_age = round(sum(ages) / len(ages), 1)
    else:
        average_age = 0

    if upcoming:
        next_birthday_name = upcoming[0]["name"]
        next_birthday_days = upcoming[0]["days"]
    else:
        next_birthday_name = "None"
        next_birthday_days = 0

    return render_template(
        "index.html",
        upcoming=upcoming,
        monthly_counts=monthly_counts,
        total_birthdays=total_birthdays,
        birthdays_today_count=birthdays_today_count,
        birthdays_this_month=birthdays_this_month,
        upcoming_this_week=upcoming_this_week,
        next_birthday_name=next_birthday_name,
        next_birthday_days=next_birthday_days,
        oldest_person=oldest_person,
        oldest_age=oldest_age,
        youngest_person=youngest_person,
        youngest_age=youngest_age,
        average_age=average_age
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        )

        if "@" not in email:
            flash("Enter a valid email address")
            return redirect("/register")

        if cursor.fetchone():
            flash("Email already exists")
            conn.close()
            return redirect("/register")

        hashed = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (email,password,verified)
            VALUES (?,?,0)
        """, (email, hashed))

        conn.commit()
        conn.close()

        try:
            send_verification_email(email)
            print("Verification email sent")
        except Exception as e:
            import traceback
            traceback.print_exc()

        flash("A verification link has been sent to your email address. Please check your inbox before logging in.")
        return redirect("/login")

    return render_template("register.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip()

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=?
            """,
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            token = serializer.dumps(
                email,
                salt="password-reset"
            )

            reset_url = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            try:

                send_reset_email(
                    email,
                    reset_url
                )

                print(f"[RESET EMAIL SENT] {email}")

            except Exception as e:

                print(
                    f"[RESET EMAIL ERROR] {email}: {e}"
                )

        flash(
            "If an account with that email exists, a password reset link has been sent."
        )

        return redirect("/login")

    return render_template(
        "forgot_password.html"
    )

@app.route("/verify/<token>")
def verify_email(token):

    try:

        email = serializer.loads(
            token,
            salt="email-confirm",
            max_age=3600
        )

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET verified=1
            WHERE email=?
        """, (email,))

        conn.commit()
        conn.close()

        flash("Email verified")
        return redirect("/login")

    except Exception:
        return "Verification link expired"

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id,email,password,verified
            FROM users
            WHERE email=?
        """, (email,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            flash("User not found")
            return redirect("/login")

        if not row[3]:
            flash("Verify your email first")
            return redirect("/login")

        if check_password_hash(row[2], password):

            user = User(
                row[0],
                row[1],
                row[2],
                row[3]
            )

            login_user(user)

            return redirect("/")

        flash("Incorrect password")

    return render_template("login.html")

# ==============================
# Logout PAGE
# ==============================
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")


@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )

    except Exception:
        return "Reset link expired"

    if request.method == "POST":

        new_password = request.form["password"]

        hashed = generate_password_hash(
            new_password
        )

        conn = sqlite3.connect(
            "birthdays.db"
        )

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET password=?
            WHERE email=?
        """, (
            hashed,
            email
        ))

        conn.commit()
        conn.close()

        flash(
            "Password updated successfully."
        )

        return redirect("/login")

    return render_template(
        "reset_password.html"
    )

# ==============================
# UPCOMING PAGE
# ==============================
@app.route('/upcoming')
@login_required
def upcoming_birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, message, photo
        FROM birthdays
    """)
    rows = cursor.fetchall()
    conn.close()

    today = date.today()
    upcoming = []

    for row in rows:

        birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

        birth_year = birthday_date.year
        age = today.year - birth_year

        if (
            today.month < birthday_date.month or
            (today.month == birthday_date.month and today.day < birthday_date.day)
        ):
            age -= 1

        turning_age = age + 1

        next_birthday = date(today.year, birthday_date.month, birthday_date.day)

        if next_birthday < today:
            next_birthday = date(today.year + 1, birthday_date.month, birthday_date.day)

        days_until = (next_birthday - today).days

        if days_until <= 30:

            name = row[1]
            phone = row[2].replace("+", "").replace(" ", "").strip()
            message = row[4]
            message_text = message.replace("{name}", name)

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
                "days": days_until,
                "age": age,
                "turning_age": turning_age,
                "whatsapp_link": whatsapp_link,
                "photo": row[5] if len(row) > 5 else ""
            })

    upcoming.sort(key=lambda x: x["days"])

    return render_template("upcoming.html", upcoming=upcoming)

# ==============================
# PROFILE
# ==============================
@app.route('/profile/<int:id>')
@login_required
def profile(id):
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM birthdays WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Person not found"

    today = date.today()
    birthday_date = datetime.strptime(row[3], "%Y-%m-%d").date()

    next_birthday = date(today.year, birthday_date.month, birthday_date.day)
    if next_birthday < today:
        next_birthday = date(today.year + 1, birthday_date.month, birthday_date.day)

    days_until = (next_birthday - today).days

    age = today.year - birthday_date.year
    if today.month < birthday_date.month or (today.month == birthday_date.month and today.day < birthday_date.day):
        age -= 1

    phone = row[2].replace("+","").replace(" ","").replace("-","").strip()
    message_text = row[4].replace("{name}", row[1])
    whatsapp_link = "https://wa.me/" + phone + "?text=" + urllib.parse.quote(message_text)

    person = {
        "id": row[0],
        "name": row[1],
        "phone": row[2],
        "birthday": row[3],
        "message": row[4],
        "photo": row[5] if len(row) > 5 else "",
        "age": age,
        "turning_age": age + 1,
        "days": days_until,
        "whatsapp_link": whatsapp_link
    }

    return render_template("profile.html", person=person)

# ==============================
# ADD BIRTHDAY
# ==============================
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_birthday():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        birthday = request.form['birthday'].strip()
        message = request.form['message'].strip()
        email = request.form.get('email', '').strip()
        photo_path = ''
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{phone}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = f"/static/photos/{filename}"

        conn = sqlite3.connect('birthdays.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM birthdays WHERE phone=?", (phone,))
        if cursor.fetchone():
            conn.close()
            return "Duplicate phone"


        cursor.execute("""
        INSERT INTO birthdays
        (name, phone, birthday, message, email, photo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            phone,
            birthday,
            message,
            email,
            photo_path
        ))

        conn.commit()
        conn.close()
        flash("Birthday added successfully!")
        return redirect('/birthdays')

    return render_template('add_birthday.html')

# ==============================
# VIEW ALL
# ==============================
@app.route('/birthdays')
@login_required
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
@login_required
def delete_birthday(id):

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM birthdays WHERE id=?", (id,))

    conn.commit()
    conn.close()
    flash("Birthday deleted successfully!")
    return redirect('/birthdays')

# ==============================
# SEND NOW
# ==============================
@app.route('/send-now')
@login_required
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
@login_required
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

# ==============================
# EDIT BIRTHDAY
# ==============================
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_birthday(id):
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        birthday = request.form['birthday']
        message = request.form['message']

        cursor.execute("SELECT photo FROM birthdays WHERE id=?", (id,))
        existing = cursor.fetchone()
        photo_path = existing[0] if existing else ''

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{phone}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = f"/static/photos/{filename}"


        email = request.form['email']
        cursor.execute("""
        UPDATE birthdays
        SET name=?, phone=?, birthday=?, message=?, email=?, photo=?
        WHERE id=?
        """, (
            name,
            phone,
            birthday,
            message,
            email,
            photo_path,
            id
        ))

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
# SEND SINGLE WHATSAPP
# ==============================
@app.route('/send/<int:id>')
@login_required
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

# ==============================
# IMPORT CSV
# ==============================
@app.route('/import', methods=['GET', 'POST'])
@login_required
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
                email = row.get('Email', '').strip()

                if not name or not phone:
                    continue

                cursor.execute("""
                    INSERT INTO birthdays
                    (name, phone, birthday, message, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name,
                    phone,
                    birthday,
                    message,
                    email
                ))

            conn.commit()
            conn.close()

            return redirect('/birthdays')

    return render_template('import.html')

# ==============================
# SEARCH
# ==============================
@app.route('/search')
@login_required
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

    return render_template('birthdays.html', birthdays=results)

# ==============================
# MONTH FILTER
# ==============================
@app.route('/month-filter')
@login_required
def month_filter():

    month = request.args.get('month')

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM birthdays
        WHERE strftime('%m', birthday) = ?
    """, (month.zfill(2),))

    birthdays = cursor.fetchall()
    conn.close()

    return render_template('birthdays.html', birthdays=birthdays)

# ==============================
# EXPORT CSV
# ==============================
@app.route('/export')
@login_required
def export_birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, phone, birthday, message, email
        FROM birthdays
    """)

    rows = cursor.fetchall()
    conn.close()

    def generate():
        yield "Name,Phone,Birthday,Message,Email\n"
        for row in rows:
            yield (
                f'"{row[0]}",'
                f'"{row[1]}",'
                f'"{row[2]}",'
                f'"{row[3]}",'
                f'"{row[4]}"\n'
            )

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=birthdays.csv"}
    )

# ==============================
# CALENDAR
# ==============================
@app.route('/calendar')
@login_required
def calendar_view():
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, birthday, id
        FROM birthdays
        ORDER BY strftime('%m-%d', birthday)
    """)

    birthdays = cursor.fetchall()
    conn.close()

    return render_template('calendar.html', birthdays=birthdays)

# ==============================
# SEND EMAIL NOW
# ==============================
@app.route('/send-email/<int:id>', methods=['GET', 'POST'])
@login_required

def send_email_now(id):
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM birthdays WHERE id=?", (id,))
    row = cursor.fetchone()

    cursor.execute("SELECT * FROM templates")
    templates = cursor.fetchall()
    conn.close()

    if row is None:
        return "Person not found"

    if request.method == 'POST':
        to_email = request.form['email'].strip()
        message = request.form['message'].strip()

        name = row[1]
        final_message = message.replace("{name}", name)
        success = send_email(to_email, name, final_message)
        return render_template('email_sent.html', name=name, email=to_email, error=not success)

    default_message = row[4].replace("{name}", row[1]) if row[4] else f"Happy Birthday {row[1]}! 🎉"
    return render_template('send_email.html', birthday=row, default_message=default_message, templates=templates)


# ==============================
# MESSAGE TEMPLATES
# ==============================
@app.route('/templates')
@login_required
def message_templates():
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates")
    templates = cursor.fetchall()
    conn.close()
    return render_template('templates.html', templates=templates)

@app.route('/templates/add', methods=['POST'])
@login_required
def add_template():
    name = request.form['name'].strip()
    message = request.form['message'].strip()

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO templates (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()

    return redirect('/templates')

@app.route('/templates/delete/<int:id>')
@login_required
def delete_template(id):
    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM templates WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/templates')


# ==============================
# REST API
# ==============================

@app.route('/api/birthdays', methods=['GET'])
@login_required
def api_birthdays():

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, email
        FROM birthdays
    """)

    rows = cursor.fetchall()
    conn.close()

    birthdays = []

    for row in rows:
        birthdays.append({
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "birthday": row[3],
            "email": row[4]
        })

    return jsonify(birthdays)

@app.route('/api/birthdays/<int:id>', methods=['GET'])
@login_required
def api_birthday(id):

    conn = sqlite3.connect('birthdays.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, birthday, email
        FROM birthdays
        WHERE id=?
    """, (id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": row[0],
        "name": row[1],
        "phone": row[2],
        "birthday": row[3],
        "email": row[4]
    })
# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, use_reloader=False)