import streamlit as st
import smtplib
import random
import time
import re
import secrets
import requests

from email.message import EmailMessage
from twilio.rest import Client


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PragyanAI OTP Verification",
    page_icon="🔐",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        font-size: 18px;
        margin-bottom: 25px;
    }

    .status-box {
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: 600;
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🔐 PragyanAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Multi-Channel OTP Verification System'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# READ SECRETS
# ============================================================

EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_VERIFY_SERVICE_SID = st.secrets["TWILIO_VERIFY_SERVICE_SID"]

TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]


# ============================================================
# TWILIO CLIENT
# ============================================================

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "email_otp_hash": None,
    "email_otp_time": None,
    "email_verified": False,

    "telegram_otp_hash": None,
    "telegram_otp_time": None,
    "telegram_verified": False,

    "email_attempts": 0,
    "telegram_attempts": 0,

    "sms_sent": False,
    "sms_verified": False,

    "whatsapp_sent": False,
    "whatsapp_verified": False,

    "last_sms_phone": "",
    "last_whatsapp_phone": ""
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def valid_email(email):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(pattern, email) is not None


def valid_phone(phone):

    # E.164-style validation
    pattern = r"^\+[1-9]\d{7,14}$"

    return re.match(pattern, phone) is not None


def generate_otp():

    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(otp):

    # Simple SHA-256 hash for keeping the OTP itself
    # out of Streamlit session state.
    import hashlib

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def check_otp(stored_hash, entered_otp):

    return (
        stored_hash is not None
        and hash_otp(entered_otp) == stored_hash
    )


# ============================================================
# EMAIL OTP
# ============================================================

def send_email_otp(receiver_email):

    if not receiver_email:

        return False, "❌ Please enter your email address."

    if not valid_email(receiver_email):

        return False, "❌ Please enter a valid email address."

    try:

        otp = generate_otp()

        # Store only hash
        st.session_state.email_otp_hash = hash_otp(otp)

        st.session_state.email_otp_time = time.time()

        st.session_state.email_attempts = 0

        message = EmailMessage()

        message["Subject"] = "PragyanAI - Email Verification OTP"

        message["From"] = EMAIL_ADDRESS

        message["To"] = receiver_email

        message.set_content(
            f"""
Hello,

Your PragyanAI verification OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this OTP, please ignore this email.

Regards,
PragyanAI
"""
        )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:

            smtp.login(
                EMAIL_ADDRESS,
                EMAIL_APP_PASSWORD
            )

            smtp.send_message(message)

        return True, "✅ Email OTP sent successfully!"

    except Exception as e:

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return False, f"❌ Email OTP failed: {str(e)}"


def verify_email_otp(user_otp):

    if not user_otp:

        return False, "❌ Please enter the OTP."

    if st.session_state.email_otp_hash is None:

        return False, "❌ Please send an Email OTP first."

    if not user_otp.isdigit() or len(user_otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    # 5-minute expiry
    if time.time() - st.session_state.email_otp_time > 300:

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return False, "⏰ OTP expired. Please request a new OTP."

    # Maximum attempts
    if st.session_state.email_attempts >= 5:

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return False, "🔒 Too many attempts. Request a new OTP."

    st.session_state.email_attempts += 1

    if check_otp(
        st.session_state.email_otp_hash,
        user_otp
    ):

        st.session_state.email_verified = True

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return True, "🎉 Email verified successfully!"

    return False, "❌ Invalid Email OTP."


# ============================================================
# TWILIO SMS / WHATSAPP SEND
# ============================================================

def send_twilio_otp(phone, channel):

    if not phone:

        return False, "❌ Please enter your phone number."

    if not valid_phone(phone):

        return (
            False,
            "❌ Use international format, e.g. +919876543210."
        )

    if channel not in ["sms", "whatsapp"]:

        return False, "❌ Invalid verification channel."

    try:

        verification = (
            twilio_client
            .verify
            .v2
            .services(TWILIO_VERIFY_SERVICE_SID)
            .verifications
            .create(
                to=phone,
                channel=channel
            )
        )

        return (
            True,
            f"✅ OTP sent successfully via "
            f"{channel.upper()}."
        )

    except Exception as e:

        return False, f"❌ {channel.upper()} OTP failed: {str(e)}"


# ============================================================
# TWILIO SMS / WHATSAPP VERIFY
# ============================================================

def verify_twilio_otp(phone, otp):

    if not phone:

        return False, "❌ Please enter your phone number."

    if not otp:

        return False, "❌ Please enter the OTP."

    if not valid_phone(phone):

        return (
            False,
            "❌ Use international format, e.g. +919876543210."
        )

    if not otp.isdigit() or len(otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    try:

        result = (
            twilio_client
            .verify
            .v2
            .services(TWILIO_VERIFY_SERVICE_SID)
            .verification_checks
            .create(
                to=phone,
                code=otp
            )
        )

        if result.status == "approved":

            return True, "🎉 Phone number verified successfully!"

        return False, "❌ Invalid or expired OTP."

    except Exception as e:

        return False, f"❌ Verification failed: {str(e)}"


# ============================================================
# TELEGRAM OTP
# ============================================================

def send_telegram_otp(chat_id):

    if not chat_id:

        return False, "❌ Please enter your Telegram Chat ID."

    chat_id = chat_id.strip()

    otp = generate_otp()

    message = (
        "🔐 PragyanAI OTP Verification\n\n"
        f"Your OTP is: {otp}\n\n"
        "This OTP is valid for 5 minutes.\n"
        "Do not share this OTP with anyone."
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    try:

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message
            },
            timeout=15
        )

        data = response.json()

        if response.ok and data.get("ok"):

            st.session_state.telegram_otp_hash = hash_otp(otp)

            st.session_state.telegram_otp_time = time.time()

            st.session_state.telegram_attempts = 0

            return True, "✅ Telegram OTP sent successfully!"

        return (
            False,
            f"❌ Telegram failed: "
            f"{data.get('description', 'Unknown error')}"
        )

    except Exception as e:

        return False, f"❌ Telegram error: {str(e)}"


def verify_telegram_otp(user_otp):

    if not user_otp:

        return False, "❌ Please enter the OTP."

    if st.session_state.telegram_otp_hash is None:

        return False, "❌ Please send a Telegram OTP first."

    if not user_otp.isdigit() or len(user_otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    if time.time() - st.session_state.telegram_otp_time > 300:

        st.session_state.telegram_otp_hash = None
        st.session_state.telegram_otp_time = None

        return False, "⏰ Telegram OTP expired."

    if st.session_state.telegram_attempts >= 5:

        st.session_state.telegram_otp_hash = None
        st.session_state.telegram_otp_time = None

        return False, "🔒 Too many attempts. Request a new OTP."

    st.session_state.telegram_attempts += 1

    if check_otp(
        st.session_state.telegram_otp_hash,
        user_otp
    ):

        st.session_state.telegram_verified = True

        st.session_state.telegram_otp_hash = None
        st.session_state.telegram_otp_time = None

        return True, "🎉 Telegram verified successfully!"

    return False, "❌ Invalid Telegram OTP."


# ============================================================
# TABS
# ============================================================

email_tab, sms_tab, whatsapp_tab, telegram_tab = st.tabs(
    [
        "📧 Email",
        "📱 SMS",
        "🟢 WhatsApp",
        "✈️ Telegram"
    ]
)


# ============================================================
# EMAIL TAB
# ============================================================

with email_tab:

    st.subheader("📧 Email OTP Verification")

    st.write(
        "Receive a secure 6-digit OTP through email."
    )

    email = st.text_input(
        "Email Address",
        placeholder="example@gmail.com",
        key="email_address_input"
    )

    if st.button(
        "📨 Send Email OTP",
        key="send_email",
        use_container_width=True
    ):

        success, message = send_email_otp(email)

        if success:

            st.success(message)

            st.info(
                "📩 Check your inbox and spam folder."
            )

        else:

            st.error(message)

    email_otp = st.text_input(
        "Enter Email OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="email_otp"
    )

    if st.button(
        "✅ Verify Email",
        key="verify_email",
        use_container_width=True
    ):

        success, message = verify_email_otp(email_otp)

        if success:

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.email_verified:

        st.success("🎉 Email verification completed!")


# ============================================================
# SMS TAB
# ============================================================

with sms_tab:

    st.subheader("📱 SMS OTP Verification")

    st.write(
        "Receive a verification OTP through SMS."
    )

    sms_phone = st.text_input(
        "Phone Number",
        placeholder="+919876543210",
        key="sms_phone"
    )

    if st.button(
        "📨 Send SMS OTP",
        key="send_sms",
        use_container_width=True
    ):

        success, message = send_twilio_otp(
            sms_phone,
            "sms"
        )

        if success:

            st.session_state.sms_sent = True
            st.session_state.last_sms_phone = sms_phone

            st.success(message)

        else:

            st.error(message)

    sms_otp = st.text_input(
        "Enter SMS OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="sms_otp"
    )

    if st.button(
        "✅ Verify SMS",
        key="verify_sms",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            sms_phone,
            sms_otp
        )

        if success:

            st.session_state.sms_verified = True

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.sms_verified:

        st.success("🎉 SMS verification completed!")


# ============================================================
# WHATSAPP TAB
# ============================================================

with whatsapp_tab:

    st.subheader("🟢 WhatsApp OTP Verification")

    st.write(
        "Receive a verification OTP through WhatsApp."
    )

    st.warning(
        "WhatsApp OTP requires WhatsApp to be properly "
        "configured and enabled in your Twilio Verify Service."
    )

    whatsapp_phone = st.text_input(
        "WhatsApp Number",
        placeholder="+919876543210",
        key="whatsapp_phone"
    )

    if st.button(
        "💬 Send WhatsApp OTP",
        key="send_whatsapp",
        use_container_width=True
    ):

        success, message = send_twilio_otp(
            whatsapp_phone,
            "whatsapp"
        )

        if success:

            st.session_state.whatsapp_sent = True

            st.session_state.last_whatsapp_phone = (
                whatsapp_phone
            )

            st.success(message)

        else:

            st.error(message)

    whatsapp_otp = st.text_input(
        "Enter WhatsApp OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="whatsapp_otp"
    )

    if st.button(
        "✅ Verify WhatsApp",
        key="verify_whatsapp",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            whatsapp_phone,
            whatsapp_otp
        )

        if success:

            st.session_state.whatsapp_verified = True

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.whatsapp_verified:

        st.success(
            "🎉 WhatsApp verification completed!"
        )


# ============================================================
# TELEGRAM TAB
# ============================================================

with telegram_tab:

    st.subheader("✈️ Telegram OTP Verification")

    st.write(
        "Receive a secure OTP through your Telegram bot."
    )

    st.info(
        "Open your Telegram bot and press START before "
        "requesting an OTP."
    )

    chat_id = st.text_input(
        "Telegram Chat ID",
        placeholder="Example: 123456789",
        key="telegram_chat_id"
    )

    if st.button(
        "✈️ Send Telegram OTP",
        key="send_telegram",
        use_container_width=True
    ):

        success, message = send_telegram_otp(chat_id)

        if success:

            st.success(message)

        else:

            st.error(message)

    telegram_otp = st.text_input(
        "Enter Telegram OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="telegram_otp"
    )

    if st.button(
        "✅ Verify Telegram",
        key="verify_telegram",
        use_container_width=True
    ):

        success, message = verify_telegram_otp(
            telegram_otp
        )

        if success:

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.telegram_verified:

        st.success(
            "🎉 Telegram verification completed!"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🔐 PragyanAI OTP Verification System"
)

st.caption(
    "Credentials are loaded securely from Streamlit Secrets."
)
```
