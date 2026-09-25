import streamlit as st
import smtplib
import random
import time
import re
import requests
import hashlib
from email.message import EmailMessage
from twilio.rest import Client

st.set_page_config(page_title="PragyanAI OTP Verification", page_icon="🔐", layout="wide")

st.markdown("""
<style>
.title {text-align:center;font-size:42px;font-weight:700;}
.subtitle {text-align:center;color:#777;font-size:18px;margin-bottom:25px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🔐 PragyanAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-Channel OTP Verification System</div>', unsafe_allow_html=True)
st.divider()

try:
    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
    EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]
    TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
    TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
    TWILIO_VERIFY_SERVICE_SID = st.secrets["TWILIO_VERIFY_SERVICE_SID"]
    TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
except Exception:
    st.error("❌ Streamlit Secrets are missing or incorrectly configured.")
    st.info("Add EMAIL_ADDRESS, EMAIL_APP_PASSWORD, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID and TELEGRAM_BOT_TOKEN in Streamlit Cloud Secrets.")
    st.stop()

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

defaults = {
    "email_hash": None, "email_time": None, "email_verified": False,
    "telegram_hash": None, "telegram_time": None, "telegram_verified": False,
    "sms_verified": False, "whatsapp_verified": False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def make_otp():
    return f"{random.SystemRandom().randint(0, 999999):06d}"

def otp_hash(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def valid_email(value):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or "") is not None

def valid_phone(value):
    return re.fullmatch(r"\+[1-9]\d{7,14}", value or "") is not None

def send_email_otp(email):
    if not email:
        return False, "❌ Enter an email address."
    if not valid_email(email):
        return False, "❌ Enter a valid email address."
    try:
        otp = make_otp()
        message = EmailMessage()
        message["Subject"] = "PragyanAI - Email Verification OTP"
        message["From"] = EMAIL_ADDRESS
        message["To"] = email
        message.set_content(f"Your PragyanAI OTP is: {otp}\n\nThis OTP is valid for 5 minutes.\nDo not share this OTP with anyone.")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.send_message(message)
        st.session_state.email_hash = otp_hash(otp)
        st.session_state.email_time = time.time()
        return True, "✅ Email OTP sent successfully!"
    except Exception as e:
        return False, f"❌ Email failed: {e}"

def verify_email_otp(otp):
    if not otp:
        return False, "❌ Enter the Email OTP."
    if len(otp) != 6 or not otp.isdigit():
        return False, "❌ OTP must contain 6 digits."
    if st.session_state.email_hash is None:
        return False, "❌ Send an Email OTP first."
    if time.time() - st.session_state.email_time > 300:
        st.session_state.email_hash = None
        st.session_state.email_time = None
        return False, "⏰ OTP expired. Send a new OTP."
    if otp_hash(otp) == st.session_state.email_hash:
        st.session_state.email_verified = True
        st.session_state.email_hash = None
        st.session_state.email_time = None
        return True, "🎉 Email verified successfully!"
    return False, "❌ Invalid Email OTP."

def send_twilio_otp(phone, channel):
    if not phone:
        return False, "❌ Enter a phone number."
    if not valid_phone(phone):
        return False, "❌ Use international format, e.g. +919876543210."
    try:
        result = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(to=phone, channel=channel)
        return True, f"✅ {channel.upper()} OTP sent. Status: {result.status}"
    except Exception as e:
        return False, f"❌ {channel.upper()} failed: {e}"

def verify_twilio_otp(phone, otp):
    if not phone:
        return False, "❌ Enter a phone number."
    if not otp:
        return False, "❌ Enter the OTP."
    if not valid_phone(phone):
        return False, "❌ Use international format, e.g. +919876543210."
    if len(otp) != 6 or not otp.isdigit():
        return False, "❌ OTP must contain 6 digits."
    try:
        result = twilio_client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(to=phone, code=otp)
        if result.status == "approved":
            return True, "🎉 OTP verified successfully!"
        return False, "❌ Invalid or expired OTP."
    except Exception as e:
        return False, f"❌ Verification failed: {e}"

def send_telegram_otp(chat_id):
    if not chat_id:
        return False, "❌ Enter your Telegram Chat ID."
    otp = make_otp()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = f"🔐 PragyanAI OTP Verification\n\nYour OTP is: {otp}\n\nThis OTP is valid for 5 minutes.\nDo not share it with anyone."
    try:
        response = requests.post(url, json={"chat_id": chat_id.strip(), "text": text}, timeout=15)
        data = response.json()
        if response.ok and data.get("ok"):
            st.session_state.telegram_hash = otp_hash(otp)
            st.session_state.telegram_time = time.time()
            return True, "✅ Telegram OTP sent successfully!"
        return False, f"❌ Telegram failed: {data.get('description', 'Unknown error')}"
    except Exception as e:
        return False, f"❌ Telegram failed: {e}"

def verify_telegram_otp(otp):
    if not otp:
        return False, "❌ Enter the Telegram OTP."
    if len(otp) != 6 or not otp.isdigit():
        return False, "❌ OTP must contain 6 digits."
    if st.session_state.telegram_hash is None:
        return False, "❌ Send a Telegram OTP first."
    if time.time() - st.session_state.telegram_time > 300:
        st.session_state.telegram_hash = None
        st.session_state.telegram_time = None
        return False, "⏰ Telegram OTP expired."
    if otp_hash(otp) == st.session_state.telegram_hash:
        st.session_state.telegram_verified = True
        st.session_state.telegram_hash = None
        st.session_state.telegram_time = None
        return True, "🎉 Telegram verified successfully!"
    return False, "❌ Invalid Telegram OTP."

email_tab, sms_tab, whatsapp_tab, telegram_tab = st.tabs(["📧 Email", "📱 SMS", "🟢 WhatsApp", "✈️ Telegram"])

with email_tab:
    st.subheader("📧 Email OTP Verification")
    email = st.text_input("Email Address", placeholder="example@gmail.com", key="email_input")
    if st.button("📨 Send Email OTP", key="email_send", use_container_width=True):
        ok, msg = send_email_otp(email)
        (st.success if ok else st.error)(msg)
    email_otp = st.text_input("Enter Email OTP", max_chars=6, type="password", key="email_otp")
    if st.button("✅ Verify Email", key="email_verify", use_container_width=True):
        ok, msg = verify_email_otp(email_otp)
        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
    if st.session_state.email_verified:
        st.success("🎉 Email verification completed!")

with sms_tab:
    st.subheader("📱 SMS OTP Verification")
    sms_phone = st.text_input("Phone Number", placeholder="+919876543210", key="sms_phone")
    if st.button("📨 Send SMS OTP", key="sms_send", use_container_width=True):
        ok, msg = send_twilio_otp(sms_phone, "sms")
        (st.success if ok else st.error)(msg)
    sms_otp = st.text_input("Enter SMS OTP", max_chars=6, type="password", key="sms_otp")
    if st.button("✅ Verify SMS", key="sms_verify", use_container_width=True):
        ok, msg = verify_twilio_otp(sms_phone, sms_otp)
        if ok:
            st.session_state.sms_verified = True
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
    if st.session_state.sms_verified:
        st.success("🎉 SMS verification completed!")

with whatsapp_tab:
    st.subheader("🟢 WhatsApp OTP Verification")
    st.warning("Your Twilio Verify Service must have WhatsApp enabled and configured.")
    whatsapp_phone = st.text_input("WhatsApp Number", placeholder="+919876543210", key="whatsapp_phone")
    if st.button("💬 Send WhatsApp OTP", key="whatsapp_send", use_container_width=True):
        ok, msg = send_twilio_otp(whatsapp_phone, "whatsapp")
        (st.success if ok else st.error)(msg)
    whatsapp_otp = st.text_input("Enter WhatsApp OTP", max_chars=6, type="password", key="whatsapp_otp")
    if st.button("✅ Verify WhatsApp", key="whatsapp_verify", use_container_width=True):
        ok, msg = verify_twilio_otp(whatsapp_phone, whatsapp_otp)
        if ok:
            st.session_state.whatsapp_verified = True
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
    if st.session_state.whatsapp_verified:
        st.success("🎉 WhatsApp verification completed!")

with telegram_tab:
    st.subheader("✈️ Telegram OTP Verification")
    st.info("Open your Telegram bot and press START before sending an OTP.")
    chat_id = st.text_input("Telegram Chat ID", placeholder="Example: 123456789", key="telegram_chat_id")
    if st.button("✈️ Send Telegram OTP", key="telegram_send", use_container_width=True):
        ok, msg = send_telegram_otp(chat_id)
        (st.success if ok else st.error)(msg)
    telegram_otp = st.text_input("Enter Telegram OTP", max_chars=6, type="password", key="telegram_otp")
    if st.button("✅ Verify Telegram", key="telegram_verify", use_container_width=True):
        ok, msg = verify_telegram_otp(telegram_otp)
        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
    if st.session_state.telegram_verified:
        st.success("🎉 Telegram verification completed!")

st.divider()
st.caption("🔐 PragyanAI Multi-Channel OTP Verification System")
st.caption("Credentials are loaded from Streamlit Secrets.")
