### AI Health Checker with Groq API and Google Sheets
# REstateAjman.py

import os
import json
import requests
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import tempfile
import gspread
from google.oauth2.service_account import Credentials

# Load secrets from .streamlit/secrets.toml
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
GCP_SHEET_ID = st.secrets["GCP_SHEET_ID"]
GCP_CREDENTIALS = json.loads(st.secrets.get("GCP_CREDENTIALS"))

# Google Sheets authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GCP_SHEET_ID).sheet1

# Function to call Groq API
@st.cache_data(show_spinner=False)
def get_ai_advice(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "AI did not return a valid response."
    except Exception as e:
        return f"Error occurred: {str(e)}"

# Function to create PDF report
def generate_pdf_report(name, email, inquiry, advice):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        c = canvas.Canvas(tmp_file.name, pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"Real Estate Inquiry Report")
        c.drawString(50, 780, f"Name: {name}")
        c.drawString(50, 760, f"Email: {email}")
        c.drawString(50, 740, f"Inquiry: {inquiry}")
        c.drawString(50, 720, f"Advice:")
        text = c.beginText(50, 700)
        for line in advice.splitlines():
            text.textLine(line)
        c.drawText(text)
        c.showPage()
        c.save()
        return tmp_file.name

# Function to send email
def send_email_with_pdf(receiver_email, pdf_path):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = receiver_email
    msg['Subject'] = "Your Real Estate AI Report"

    msg.attach(MIMEText("Please find attached the AI-generated advice report.", 'plain'))
    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# UI
st.title("🏠 AI-Powered Real Estate Advisor - Ajman, UAE")
st.markdown("Enter your property requirement and get smart suggestions.")

with st.form("real_estate_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Email")
    inquiry = st.text_area("Describe what you're looking for (location, type, budget)")
    submit = st.form_submit_button("Get AI Advice")

if submit:
    if not (name and email and inquiry):
        st.warning("Please fill in all fields.")
    else:
        st.info("Getting AI advice...")
        prompt = f"You are an AI real estate advisor in Ajman, UAE. A user is looking for: {inquiry}. Provide smart suggestions including potential areas and developer projects."
        advice = get_ai_advice(prompt)

        # Show response
        st.success("AI Suggestion:")
        st.write(advice)

        # Log to Google Sheets
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), name, email, inquiry, advice])

        # Generate PDF & email it
        pdf_path = generate_pdf_report(name, email, inquiry, advice)
        send_email_with_pdf(email, pdf_path)

        st.success("✅ Advice sent to your email as PDF.")

st.markdown("---")
st.caption("This service uses Groq AI, Gmail, and Google Sheets. Built for Ajman Real Estate leads.")
