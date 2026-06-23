# 🎂 Birthday Scheduler

A Flask-powered Birthday Scheduler that helps users manage birthdays, send automated greetings, and receive reminders via WhatsApp and Email.

## Features

### 👤 User Accounts

* User registration and login
* Secure password hashing
* Email verification system
* Forgot password functionality
* Password reset via email link
* Protected routes using Flask-Login

### 🎂 Birthday Management

* Add birthdays with name, phone number, email, and birth date
* Upload profile photos for contacts
* View all birthdays in a searchable table
* Edit birthday records
* Delete birthday records
* Individual profile pages for each contact

### 📅 Birthday Tracking

* Dashboard with birthday analytics
* Upcoming birthdays page
* Today's birthdays detection
* Birthdays this month statistics
* Upcoming birthdays this week
* Next birthday countdown
* Age and upcoming age calculations
* Calendar view

### 📊 Analytics Dashboard

* Total birthdays tracked
* Monthly birthday distribution
* Oldest person tracker
* Youngest person tracker
* Average age calculation
* Upcoming birthday statistics

### 💬 Messaging

* Custom birthday message templates
* Template management system
* WhatsApp message generation
* One-click WhatsApp links
* Manual WhatsApp sending
* Automated WhatsApp birthday greetings

### 📧 Email Features

* Automated birthday emails
* Manual email sending
* Email verification system
* Password reset emails
* HTML email templates

### 🔔 Notifications

* Scheduled birthday reminders
* Automated daily birthday checks
* Automatic birthday message delivery
* Manual "Send Now" option

### 📂 Data Management

* SQLite database storage
* CSV import birthdays
* CSV export birthdays
* REST API endpoints
* Search birthdays by name or phone
* Filter birthdays by month

### 🖼 Media Support

* Photo uploads
* Birthday profile pictures
* Secure image handling

### ⚙️ Automation

* APScheduler background jobs
* Daily birthday message scheduling
* Delivery logging to prevent duplicate sends

### 🌐 API

* Get all birthdays via API
* Get birthday by ID via API
* JSON responses

## Technologies Used

* Python
* Flask
* Flask-Login
* SQLite
* Twilio API
* SMTP Email
* APScheduler
* HTML/CSS/JavaScript
* Bootstrap
* Jinja2 Templates

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Mister-MeToo/birthday-scheduler.git
cd birthday-scheduler
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Create Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_secret_key

EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

### 6. Initialize Database

```bash
python create_db.py
```

### 7. Run the Application

```bash
python app.py
```

### 8. Open in Browser

```text
http://127.0.0.1:5000
```

## Default Scheduler Jobs

* Checks birthdays every minute
* Sends birthday messages automatically at 09:00 AM
* Prevents duplicate sends using delivery logs

## Future Improvements

* Cloud deployment
* Multi-user birthday collections
* SMS notifications
* Google Calendar integration
* Advanced analytics dashboard
* Mobile application

