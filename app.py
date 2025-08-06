from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os
import smtplib
from email.mime.text import MIMEText
import pandas as pd

app = Flask(__name__)

DATA_FILE = 'data.json'
HTR_FILE = 'htr_counter.txt'
# Use your exact absolute path for the Excel file (use raw string r'...' to avoid escaping issues)
EXCEL_FILE = r'C:\Users\sneha\Downloads\HTR_CODE\HTR-BACKEND\DATA.xlsx'
MANAGER_EMAIL = 'msn@juniper.net'  # Replace with actual manager email

# Initialize counter file if not exists
if not os.path.exists(HTR_FILE):
    with open(HTR_FILE, 'w') as f:
        f.write('HTR05237')

# Initialize JSON data file if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

def get_next_htr_number():
    with open(HTR_FILE, 'r+') as f:
        last_htr = f.read().strip()
        num = int(last_htr[3:]) + 1
        next_htr = f"HTR{num:05d}"
        f.seek(0)
        f.write(next_htr)
        f.truncate()
    return next_htr

@app.route("/submit", methods=["POST"])
def submit_form():
    form_data = request.form.to_dict()
    submission_id = str(len(load_data()) + 1)

    save_submission(submission_id, form_data)

    # Append submitted data as a row in your local Excel file
    append_to_excel(form_data)

    # Generate review link
    review_link = f"{request.host_url}review/{submission_id}"

    # Notify manager by email
    send_email_to_manager(review_link)

    return "Form submitted successfully. Manager will review it soon."

@app.route("/review/<submission_id>")
def review(submission_id):
    data = load_data().get(submission_id)
    if not data:
        return "Submission not found."

    html = f"""
    <h2>HTR Review for Submission {submission_id}</h2>
    <ul>
        {''.join(f'<li><strong>{k}</strong>: {v}</li>' for k, v in data.items())}
    </ul>
    <form action="/generate_htr/{submission_id}" method="POST">
        <button type="submit">Generate HTR Number</button>
    </form>
    """
    return render_template_string(html)

@app.route("/generate_htr/<submission_id>", methods=["POST"])
def generate_htr(submission_id):
    data = load_data()
    if submission_id not in data:
        return "Submission not found."

    htr_number = get_next_htr_number()
    data[submission_id]["HTR Number"] = htr_number
    save_all_data(data)

    # Send notification email to user who submitted form
    user_email = data[submission_id].get("requestor_email")
    if user_email:
        send_notification_to_user(user_email, htr_number)

    return f"""
    <h2>HTR Number Generated: {htr_number}</h2><br>
    <a href='/review/{submission_id}'>Back</a>
    """

def append_to_excel(form_data):
    new_df = pd.DataFrame([form_data])
    if os.path.exists(EXCEL_FILE):
        # Read existing file
        existing_df = pd.read_excel(EXCEL_FILE)
        # Append new row, align columns
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_excel(EXCEL_FILE, index=False)
    else:
        # Create new Excel file with headers
        new_df.to_excel(EXCEL_FILE, index=False)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_submission(submission_id, data):
    all_data = load_data()
    all_data[submission_id] = data
    save_all_data(all_data)

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_email_to_manager(link):
    sender_email = "snehmani7310@gmail.com"  # Replace with your email
    sender_password = "Sneha@2001"  # Replace with your email app password
    subject = "New HTR Form Submission"
    body = f"A new form has been submitted.\n\nReview it here: {link}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = MANAGER_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ Email sent to {MANAGER_EMAIL}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

def send_notification_to_user(user_email, htr_number):
    sender_email = "snehmani7310@gmail.com"  # Replace with your email
    sender_password = "Sneha@2001"  # Replace with your email app password
    subject = "HTR Request Approved"
    body = f"The manager ({MANAGER_EMAIL}) has approved your request.\nYour HTR Number is: {htr_number}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = user_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ Notification sent to user at {user_email}")
    except Exception as e:
        print(f"❌ Failed to send notification email: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
