# 🎂 Birthday Scheduler

A Flask-based web application that helps you store birthdays and automatically send birthday reminders via Email and WhatsApp (Twilio).

---

## 🚀 Features

- Add birthdays with name, phone number, and date
- View all saved birthdays in a table
- Edit or delete existing entries
- Automatically detect today’s birthdays
- Custom birthday message templates
- Email notifications (SMTP)
- WhatsApp notifications (Twilio API)
- Manual “Send Now” button
- SQLite database storage

---

## 🔔 Notification System

### Email (SMTP)
- Sends personalized birthday messages
- Uses Python SMTP/email libraries

### WhatsApp (Twilio)
- Sends automated WhatsApp messages
- Uses Twilio API

⚠️ Credentials are NOT included for security reasons.

---

## 🛠️ Tech Stack

- Python
- Flask
- SQLite
- HTML / Jinja2
- Twilio API
- SMTP Email

---

## 📁 Project Structure

BirthdayScheduler/
├── app.py
├── scheduler.py
├── create_db.py
├── email_sender.py
├── birthdays.db
├── templates/
└── static/

---

## ▶️ How to Run

git clone https://github.com/YOUR_USERNAME/birthday-scheduler.git
cd birthday-scheduler

python -m venv venv
venv\Scripts\activate

pip install flask twilio

python app.py

Open:
http://127.0.0.1:5000/

---

## 📌 Future Improvements

- Deploy online
- Add login system
- Calendar view
- Background scheduler (Celery/APScheduler)
- SMS notifications

---


