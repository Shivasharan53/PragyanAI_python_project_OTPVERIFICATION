import streamlit as st
import smtplib
import random
import time
import re
import requests
import hashlib

from email.message import EmailMessage
from twilio.rest import Client


# ============================================================
# PAGE CONFIG
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
    .title {
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

    .info-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🔐 PragyanAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Multi-Channel OTP Verification System</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# LOAD SECRETS
# ============================================================

try:
    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]
    EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

    TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
    TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
    TWILIO_VERIFY_SERVICE_SID = st.secrets[
        "TWILIO_VERIFY_SERVICE_SID"
    ]

    TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

except Exception as e:

    st.error(
        "❌ Streamlit Secrets are missing or incorrectly configured."
    )

    st.info(
        "Go to Streamlit Cloud → Settings → Secrets "
        "and check the required secret names."
    )

    st.stop()


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

session_defaults = {

    "email_otp_hash": None,
    "email_otp_time": None,
    "email_verified": False,

    "telegram_otp_hash": None,
    "telegram_otp_time": None,
    "telegram_verified": False,

    "sms_verified": False,
    "whatsapp_verified": False,

    "sms_sent": False,
    "whatsapp_sent": False
}


for key, value in session_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_otp():

    return str(random.randint(100000, 999999))


def hash_otp(otp):

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def validate_email(email):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(pattern, email) is not None


def validate_phone(phone):

    pattern = r"^\+[1-9]\d{7,14}$"

    return re.match(pattern, phone) is not None


# ============================================================
# EMAIL OTP
# ============================================================

def send_email_otp(receiver_email):

    if not receiver_email:

        return False, "❌ Please enter your email address."

    if not validate_email(receiver_email):

        return False, "❌ Please enter a valid email address."

    try:

        otp = generate_otp()

        st.session_state.email_otp_hash = hash_otp(otp)

        st.session_state.email_otp_time = time.time()

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

Please do not share this OTP with anyone.

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

    if not user_otp.isdigit() or len(user_otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    if st.session_state.email_otp_hash is None:

        return False, "❌ Please send an Email OTP first."

    if (
        time.time()
        - st.session_state.email_otp_time
        > 300
    ):

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return False, "⏰ OTP expired. Please request a new OTP."

    if (
        hash_otp(user_otp)
        == st.session_state.email_otp_hash
    ):

        st.session_state.email_verified = True

        st.session_state.email_otp_hash = None
        st.session_state.email_otp_time = None

        return True, "🎉 Email verified successfully!"

    return False, "❌ Invalid Email OTP."


# ============================================================
# TWILIO SMS / WHATSAPP
# ============================================================

def send_twilio_otp(phone, channel):

    if not phone:

        return False, "❌ Please enter your phone number."

    if not validate_phone(phone):

        return (
            False,
            "❌ Use international format like +919876543210."
        )

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
            f"✅ {channel.upper()} OTP sent successfully!"
        )

    except Exception as e:

        return (
            False,
            f"❌ {channel.upper()} OTP failed: {str(e)}"
        )


def verify_twilio_otp(phone, otp):

    if not phone:

        return False, "❌ Please enter your phone number."

    if not otp:

        return False, "❌ Please enter the OTP."

    if not validate_phone(phone):

        return (
            False,
            "❌ Use international format like +919876543210."
        )

    if not otp.isdigit() or len(otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    try:

        verification_check = (
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

        if verification_check.status == "approved":

            return True, "🎉 OTP verified successfully!"

        return False, "❌ Invalid or expired OTP."

    except Exception as e:

        return (
            False,
            f"❌ OTP verification failed: {str(e)}"
        )


# ============================================================
# TELEGRAM OTP
# ============================================================

def send_telegram_otp(chat_id):

    if not chat_id:

        return False, "❌ Please enter your Telegram Chat ID."

    otp = generate_otp()

    message = (
        "🔐 PragyanAI OTP Verification\n\n"
        f"Your OTP is: {otp}\n\n"
        "This OTP is valid for 5 minutes.\n"
        "Do not share this OTP with anyone."
    )

    url = (
        "https://api.telegram.org/"
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

            st.session_state.telegram_otp_hash = hash_otp(
                otp
            )

            st.session_state.telegram_otp_time = time.time()

            return (
                True,
                "✅ Telegram OTP sent successfully!"
            )

        return (
            False,
            "❌ Telegram failed: "
            + str(
                data.get(
                    "description",
                    "Unknown error"
                )
            )
        )

    except Exception as e:

        return False, f"❌ Telegram error: {str(e)}"


def verify_telegram_otp(user_otp):

    if not user_otp:

        return False, "❌ Please enter the OTP."

    if not user_otp.isdigit() or len(user_otp) != 6:

        return False, "❌ OTP must contain exactly 6 digits."

    if st.session_state.telegram_otp_hash is None:

        return False, "❌ Please send Telegram OTP first."

    if (
        time.time()
        - st.session_state.telegram_otp_time
        > 300
    ):

        st.session_state.telegram_otp_hash = None
        st.session_state.telegram_otp_time = None

        return False, "⏰ Telegram OTP expired."

    if (
        hash_otp(user_otp)
        == st.session_state.telegram_otp_hash
    ):

        st.session_state.telegram_verified = True

        st.session_state.telegram_otp_hash = None
        st.session_state.telegram_otp_time = None

        return (
            True,
            "🎉 Telegram verified successfully!"
        )

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

    email = st.text_input(
        "Email Address",
        placeholder="example@gmail.com",
        key="email_input"
    )

    if st.button(
        "📨 Send Email OTP",
        key="email_send",
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
        key="email_otp_input"
    )

    if st.button(
        "✅ Verify Email",
        key="email_verify",
        use_container_width=True
    ):

        success, message = verify_email_otp(
            email_otp
        )

        if success:

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.email_verified:

        st.success(
            "🎉 Email verification completed!"
        )


# ============================================================
# SMS TAB
# ============================================================

with sms_tab:

    st.subheader("📱 SMS OTP Verification")

    phone_sms = st.text_input(
        "Phone Number",
        placeholder="+919876543210",
        key="sms_phone"
    )

    if st.button(
        "📨 Send SMS OTP",
        key="sms_send",
        use_container_width=True
    ):

        success, message = send_twilio_otp(
            phone_sms,
            "sms"
        )

        if success:

            st.session_state.sms_sent = True

            st.success(message)

        else:

            st.error(message)

    sms_otp = st.text_input(
        "Enter SMS OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="sms_otp_input"
    )

    if st.button(
        "✅ Verify SMS",
        key="sms_verify",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            phone_sms,
            sms_otp
        )

        if success:

            st.session_state.sms_verified = True

            st.success(message)

            st.balloons()

        else:

            st.error(message)

    if st.session_state.sms_verified:

        st.success(
            "🎉 SMS verification completed!"
        )


# ============================================================
# WHATSAPP TAB
# ============================================================

with whatsapp_tab:

    st.subheader("🟢 WhatsApp OTP Verification")

    st.warning(
        "WhatsApp must be enabled and configured "
        "in your Twilio Verify Service."
    )

    phone_whatsapp = st.text_input(
        "WhatsApp Number",
        placeholder="+919876543210",
        key="whatsapp_phone"
    )

    if st.button(
        "💬 Send WhatsApp OTP",
        key="whatsapp_send",
        use_container_width=True
    ):

        success, message = send_twilio_otp(
            phone_whatsapp,
            "whatsapp"
        )

        if success:

            st.session_state.whatsapp_sent = True

            st.success(message)

        else:

            st.error(message)

    whatsapp_otp = st.text_input(
        "Enter WhatsApp OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="whatsapp_otp_input"
    )

    if st.button(
        "✅ Verify WhatsApp",
        key="whatsapp_verify",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            phone_whatsapp,
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

    st.info(
        "Open your Telegram bot and press START first."
    )

    chat_id = st.text_input(
        "Telegram Chat ID",
        placeholder="Example: 123456789",
        key="telegram_chat_id"
    )

    if st.button(
        "✈️ Send Telegram OTP",
        key="telegram_send",
        use_container_width=True
    ):

        success, message = send_telegram_otp(
            chat_id
        )

        if success:

            st.success(message)

        else:

            st.error(message)

    telegram_otp = st.text_input(
        "Enter Telegram OTP",
        placeholder="6-digit OTP",
        max_chars=6,
        type="password",
        key="telegram_otp_input"
    )

    if st.button(
        "✅ Verify Telegram",
        key="telegram_verify",
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
    "🔐 PragyanAI Multi-Channel OTP Verification System"
)

st.caption(
    "Credentials are loaded from Streamlit Secrets."
)
```
