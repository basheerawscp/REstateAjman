### AI Real Estate Advisor - Streamlit App with Region & Budget Filters
# app.py

import os
import streamlit as st
from datetime import datetime
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import gspread
from google.oauth2.service_account import Credentials

# Load secrets
TOGETHER_API_KEY = st.secrets.get("TOGETHER_API_KEY")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
EMAIL_ADDRESS = st.secrets.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD")
GCP_SHEET_ID = st.secrets.get("GCP_SHEET_ID")
GCP_CREDENTIALS = json.loads(st.secrets.get("GCP_CREDENTIALS"))

# Google Sheets Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GCP_SHEET_ID).sheet1

# Streamlit App UI
st.set_page_config(page_title="UAE Real Estate AI Advisor", page_icon="🏠")
st.title("🏠 AI Real Estate Advisor - Ajman")
st.markdown("Use AI to find the best property deals in Ajman based on your preferences.")

# User Input Form
with st.form("lead_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")

    ajman_areas = [
        "Al Nuaimiya", "Al Rashidiya", "Al Mowaihat", "Al Jurf",
        "Al Rawda", "Emirates City", "Ajman Corniche", "Al Zahra", "Helio", "Masfout"
    ]
    region = st.selectbox("Preferred Area in Ajman", ajman_areas)

    budget_min = st.number_input("Minimum Budget (AED)", min_value=10000, max_value=10000000, value=100000)
    budget_max = st.number_input("Maximum Budget (AED)", min_value=budget_min, max_value=10000000, value=500000)

    message = st.text_area("Describe what you're looking for")
    submit = st.form_submit_button("Find Properties")

# On Submit
if submit and name and email and message:
    with st.spinner("Thinking like a property expert..."):
        prompt = f"""
        Act as a UAE real estate AI advisor. Suggest ideal property types, location benefits, and investment insights.

        Name: {name}
        Preferred Area: {region}
        Budget Range: AED {budget_min} - {budget_max}
        Preferences: {message}

        Suggest suitable properties, add area advantages, and explain investment potential. Use a professional yet friendly tone.
        """

        try:
            response = requests.post(
                url="https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            result = response.json()
            reply = result['choices'][0]['message']['content'].strip()

            st.success("Here's what the AI suggests:")
            st.write(reply)

            # Log to Google Sheets
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([name, email, region, budget_min, budget_max, message, now])

            # Generate PDF
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            pdf.drawString(72, 800, f"Real Estate AI Report - {name}")
            pdf.drawString(72, 780, f"Email: {email}")
            pdf.drawString(72, 760, f"Area: {region}, Budget: AED {budget_min} - {budget_max}")
            text = pdf.beginText(72, 740)
            for line in reply.splitlines():
                text.textLine(line)
            pdf.drawText(text)
            pdf.showPage()
            pdf.save()
            buffer.seek(0)

            # Email PDF
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email
            msg['Subject'] = "Your Ajman Property Report"

            msg.attach(MIMEText("Attached is your AI property report. Contact us for personalized help!", 'plain'))
            attachment = MIMEApplication(buffer.read(), _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename="property_report.pdf")
            msg.attach(attachment)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            st.success("PDF report emailed successfully!")

        except Exception as e:
            st.error(f"Error occurred: {e}")

else:
    if submit:
        st.warning("Please fill all fields before submitting.")

# Footer
st.markdown("---")
st.markdown("© 2025 RealEstateAI | Ajman | Powered by Groq + Google Sheets")
