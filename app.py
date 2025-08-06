from flask import Flask, request, jsonify, render_template_string, redirect
import json
import os

app = Flask(__name__)

DATA_FILE = 'data.json'
HTR_FILE = 'htr_counter.txt'
MANAGER_EMAIL = 'msn@juniper.net'  # Change this if needed

# Initialize counter file
if not os.path.exists(HTR_FILE):
    with open(HTR_FILE, 'w') as f:
        f.write('HTR05237')

# Load stored submissions
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

    # Generate review link
    review_link = f"{request.host_url}review/{submission_id}"

    # Disable email for now — you can re-enable later
    print(f"✅ Form submitted. Review link: {review_link}")
    
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

    return f"<h2>HTR Number Generated: {htr_number}</h2><br><a href='/review/{submission_id}'>Back</a>"

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

# (Optional) Enable this later when you're ready to email from server
# def send_email_to_manager(link):
#     sender_email = "YOUR_EMAIL@gmail.com"
#     sender_password = "YOUR_APP_PASSWORD"
#     subject = "New HTR Form Submission"
#     body = f"A new form has been submitted.\n\nReview it here: {link}"
#     msg = MIMEText(body)
#     msg["Subject"] = subject
#     msg["From"] = sender_email
#     msg["To"] = MANAGER_EMAIL
#     try:
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(sender_email, sender_password)
#             server.send_message(msg)
#         print("✅ Email sent.")
#     except Exception as e:
#         print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

