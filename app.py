import streamlit as st
import smtplib
import random
import time
import hashlib
import re

from email.message import EmailMessage
from twilio.rest import Client


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PragyanAI OTP Security",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PROFESSIONAL LIGHT UI
# ============================================================

st.markdown(
    """
    <style>

    /* ================================
       MAIN APPLICATION
       ================================ */

    .stApp {
        background-color: #f5f7fb !important;
        color: #111827 !important;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* ================================
       MAIN HEADINGS
       ================================ */

    .main h1,
    .main h2,
    .main h3,
    .main h4 {
        color: #111827 !important;
    }

    .main h1 {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
    }

    .main h2 {
        font-size: 1.8rem !important;
        font-weight: 750 !important;
    }

    .main h3 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }


    /* ================================
       MAIN TEXT
       ================================ */

    .main p {
        color: #374151 !important;
    }

    .main span {
        color: inherit;
    }

    .main label {
        color: #111827 !important;
        font-weight: 600 !important;
    }


    /* ================================
       CAPTION
       ================================ */

    [data-testid="stCaptionContainer"] {
        color: #6b7280 !important;
    }


    /* ================================
       DIVIDER
       ================================ */

    .main hr {
        border-color: #d1d5db !important;
    }


    /* ================================
       INPUT
       ================================ */

    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
    }

    .main input {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 10px !important;
    }

    .main input::placeholder {
        color: #9ca3af !important;
    }


    /* ================================
       MAIN BUTTONS
       ================================ */

    .main .stButton button {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #111827 !important;
        border-radius: 10px !important;
        min-height: 46px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    .main .stButton button p {
        color: #ffffff !important;
    }

    .main .stButton button:hover {
        background-color: #374151 !important;
        border-color: #374151 !important;
    }


    /* ================================
       METRIC CARDS
       ================================ */

    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06) !important;
    }

    div[data-testid="stMetric"] label {
        color: #4b5563 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
    }


    /* ================================
       ALERT BOXES
       ================================ */

    div[data-testid="stAlert"] {
        border-radius: 12px !important;
    }


    /* ================================
       SIDEBAR
       ================================ */

    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] p {
        color: #e5e7eb !important;
    }

    section[data-testid="stSidebar"] span {
        color: #e5e7eb !important;
    }


    /* ================================
       SIDEBAR BUTTONS
       ================================ */

    section[data-testid="stSidebar"] .stButton button {
        width: 100% !important;
        min-height: 48px !important;
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stButton button p {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #374151 !important;
        border-color: #6366f1 !important;
    }


    /* ================================
       SIDEBAR DIVIDERS
       ================================ */

    section[data-testid="stSidebar"] hr {
        border-color: #374151 !important;
    }


    /* ================================
       HIDE STREAMLIT FOOTER
       ================================ */

    footer {
        visibility: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "email_hash" not in st.session_state:
    st.session_state.email_hash = None

if "email_created" not in st.session_state:
    st.session_state.email_created = None

if "email_verified" not in st.session_state:
    st.session_state.email_verified = False

if "sms_verified" not in st.session_state:
    st.session_state.sms_verified = False

if "whatsapp_verified" not in st.session_state:
    st.session_state.whatsapp_verified = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🔐 PragyanAI")

    st.caption("OTP Security Platform")

    st.divider()

    st.subheader("Navigation")

    if st.button(
        "🏠  Dashboard",
        key="sidebar_dashboard",
        use_container_width=True
    ):
        st.session_state.page = "Dashboard"
        st.rerun()

    if st.button(
        "📧  Email Verification",
        key="sidebar_email",
        use_container_width=True
    ):
        st.session_state.page = "Email"
        st.rerun()

    if st.button(
        "📱  SMS Verification",
        key="sidebar_sms",
        use_container_width=True
    ):
        st.session_state.page = "SMS"
        st.rerun()

    if st.button(
        "🟢  WhatsApp Verification",
        key="sidebar_whatsapp",
        use_container_width=True
    ):
        st.session_state.page = "WhatsApp"
        st.rerun()

    st.divider()

    st.subheader("Security")

    st.write("🔒 Secure credentials")
    st.write("⏱️ OTP expiry")
    st.write("🔐 OTP hashing")
    st.write("☁️ Streamlit Secrets")

    st.divider()

    st.caption("PragyanAI Security Platform")
    st.caption("Email • SMS • WhatsApp")


# ============================================================
# REQUIRED SECRETS
# ============================================================

required_secrets = [
    "EMAIL_ADDRESS",
    "EMAIL_APP_PASSWORD",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_VERIFY_SERVICE_SID"
]


missing_secrets = []

for secret_name in required_secrets:

    if secret_name not in st.secrets:
        missing_secrets.append(secret_name)


if missing_secrets:

    st.title("🔐 PragyanAI")

    st.error(
        "Streamlit Secrets are not configured."
    )

    st.write(
        "Go to Streamlit Cloud → Manage app → Settings → Secrets."
    )

    st.write("Missing values:")

    for secret_name in missing_secrets:
        st.code(secret_name)

    st.stop()


# ============================================================
# READ SECRETS
# ============================================================

EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]

EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]

TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]

TWILIO_VERIFY_SERVICE_SID = st.secrets[
    "TWILIO_VERIFY_SERVICE_SID"
]


# ============================================================
# TWILIO CLIENT
# ============================================================

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_otp():

    return f"{random.SystemRandom().randint(0, 999999):06d}"


def hash_otp(otp):

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def valid_email(email):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.fullmatch(
        pattern,
        email or ""
    ) is not None


def valid_phone(phone):

    pattern = r"^\+[1-9]\d{7,14}$"

    return re.fullmatch(
        pattern,
        phone or ""
    ) is not None


def otp_expired(created_time):

    if created_time is None:
        return True

    return (
        time.time() - created_time
    ) > 300


# ============================================================
# EMAIL OTP - SEND
# ============================================================

def send_email_otp(email):

    if not email:

        return (
            False,
            "Please enter your email address."
        )

    if not valid_email(email):

        return (
            False,
            "Please enter a valid email address."
        )

    try:

        otp = generate_otp()

        message = EmailMessage()

        message["Subject"] = (
            "PragyanAI - Email Verification OTP"
        )

        message["From"] = EMAIL_ADDRESS

        message["To"] = email

        message.set_content(
            f"""
Hello,

Your PragyanAI verification OTP is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

Regards,
PragyanAI Security Team
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

            smtp.send_message(
                message
            )

        st.session_state.email_hash = hash_otp(
            otp
        )

        st.session_state.email_created = time.time()

        st.session_state.email_verified = False

        return (
            True,
            "Email OTP sent successfully."
        )

    except Exception as error:

        return (
            False,
            f"Email sending failed: {error}"
        )


# ============================================================
# EMAIL OTP - VERIFY
# ============================================================

def verify_email_otp(otp):

    if not otp:

        return (
            False,
            "Please enter the Email OTP."
        )

    if not otp.isdigit() or len(otp) != 6:

        return (
            False,
            "OTP must contain exactly 6 digits."
        )

    if st.session_state.email_hash is None:

        return (
            False,
            "Please send an Email OTP first."
        )

    if otp_expired(
        st.session_state.email_created
    ):

        st.session_state.email_hash = None
        st.session_state.email_created = None

        return (
            False,
            "OTP expired. Please request a new OTP."
        )

    if (
        hash_otp(otp)
        == st.session_state.email_hash
    ):

        st.session_state.email_verified = True

        st.session_state.email_hash = None
        st.session_state.email_created = None

        return (
            True,
            "Email verified successfully."
        )

    return (
        False,
        "Incorrect Email OTP."
    )


# ============================================================
# TWILIO - SEND OTP
# ============================================================

def send_twilio_otp(phone, channel):

    if not phone:

        return (
            False,
            "Please enter your phone number."
        )

    if not valid_phone(phone):

        return (
            False,
            "Use international format, for example +919876543210."
        )

    try:

        verification = (
            twilio_client
            .verify
            .v2
            .services(
                TWILIO_VERIFY_SERVICE_SID
            )
            .verifications
            .create(
                to=phone,
                channel=channel
            )
        )

        return (
            True,
            f"{channel.upper()} OTP sent successfully. "
            f"Status: {verification.status}"
        )

    except Exception as error:

        return (
            False,
            f"{channel.upper()} sending failed: {error}"
        )


# ============================================================
# TWILIO - VERIFY OTP
# ============================================================

def verify_twilio_otp(phone, otp):

    if not phone:

        return (
            False,
            "Please enter your phone number."
        )

    if not valid_phone(phone):

        return (
            False,
            "Use international format, for example +919876543210."
        )

    if not otp:

        return (
            False,
            "Please enter the OTP."
        )

    if not otp.isdigit() or len(otp) != 6:

        return (
            False,
            "OTP must contain exactly 6 digits."
        )

    try:

        verification = (
            twilio_client
            .verify
            .v2
            .services(
                TWILIO_VERIFY_SERVICE_SID
            )
            .verification_checks
            .create(
                to=phone,
                code=otp
            )
        )

        if verification.status == "approved":

            return (
                True,
                "OTP verified successfully."
            )

        return (
            False,
            "Incorrect or expired OTP."
        )

    except Exception as error:

        return (
            False,
            f"OTP verification failed: {error}"
        )


# ============================================================
# APPLICATION HEADER
# ============================================================

st.title("🔐 PragyanAI")

st.subheader(
    "Secure Multi-Channel OTP Verification Platform"
)

st.write(
    "Verify users securely through Email, SMS and WhatsApp."
)

st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.header("🏠 Security Dashboard")

    st.write(
        "Monitor and manage your OTP verification channels."
    )

    st.divider()

    st.subheader("📊 Verification Status")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.session_state.email_verified:

            st.metric(
                "📧 Email",
                "VERIFIED"
            )

        else:

            st.metric(
                "📧 Email",
                "NOT VERIFIED"
            )

    with col2:

        if st.session_state.sms_verified:

            st.metric(
                "📱 SMS",
                "VERIFIED"
            )

        else:

            st.metric(
                "📱 SMS",
                "NOT VERIFIED"
            )

    with col3:

        if st.session_state.whatsapp_verified:

            st.metric(
                "🟢 WhatsApp",
                "VERIFIED"
            )

        else:

            st.metric(
                "🟢 WhatsApp",
                "NOT VERIFIED"
            )

    st.write("")

    st.divider()

    st.subheader("🚀 Quick Actions")

    st.write(
        "Choose a verification channel to continue."
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "📧  Email Verification",
            key="dashboard_email",
            use_container_width=True
        ):

            st.session_state.page = "Email"

            st.rerun()

    with col2:

        if st.button(
            "📱  SMS Verification",
            key="dashboard_sms",
            use_container_width=True
        ):

            st.session_state.page = "SMS"

            st.rerun()

    with col3:

        if st.button(
            "🟢  WhatsApp Verification",
            key="dashboard_whatsapp",
            use_container_width=True
        ):

            st.session_state.page = "WhatsApp"

            st.rerun()

    st.write("")

    st.info(
        "🔒 Your credentials are stored using "
        "Streamlit Secrets and are not written into the application code."
    )


# ============================================================
# EMAIL VERIFICATION
# ============================================================

elif st.session_state.page == "Email":

    st.header("📧 Email Verification")

    st.write(
        "Send a secure six-digit OTP to an email address."
    )

    st.divider()

    email = st.text_input(
        "Email Address",
        placeholder="example@gmail.com",
        key="email_address_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_email_button = st.button(
            "📨 Send Email OTP",
            key="email_send_button",
            use_container_width=True
        )

    with col2:

        resend_email_button = st.button(
            "🔄 Resend Email OTP",
            key="email_resend_button",
            use_container_width=True
        )

    if (
        send_email_button
        or resend_email_button
    ):

        success, message = send_email_otp(
            email
        )

        if success:

            st.success(
                f"✅ {message}"
            )

        else:

            st.error(
                f"❌ {message}"
            )

    st.write("")

    email_otp = st.text_input(
        "Enter Email OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="email_otp_input"
    )

    if st.button(
        "✅ Verify Email OTP",
        key="email_verify_button",
        use_container_width=True
    ):

        success, message = verify_email_otp(
            email_otp
        )

        if success:

            st.success(
                f"🎉 {message}"
            )

            st.balloons()

        else:

            st.error(
                f"❌ {message}"
            )


# ============================================================
# SMS VERIFICATION
# ============================================================

elif st.session_state.page == "SMS":

    st.header("📱 SMS Verification")

    st.write(
        "Send a secure six-digit OTP to a mobile number."
    )

    st.divider()

    sms_phone = st.text_input(
        "Mobile Number",
        placeholder="+919876543210",
        key="sms_phone_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_sms_button = st.button(
            "📨 Send SMS OTP",
            key="sms_send_button",
            use_container_width=True
        )

    with col2:

        resend_sms_button = st.button(
            "🔄 Resend SMS OTP",
            key="sms_resend_button",
            use_container_width=True
        )

    if (
        send_sms_button
        or resend_sms_button
    ):

        success, message = send_twilio_otp(
            sms_phone,
            "sms"
        )

        if success:

            st.success(
                f"✅ {message}"
            )

        else:

            st.error(
                f"❌ {message}"
            )

    st.write("")

    sms_otp = st.text_input(
        "Enter SMS OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="sms_otp_input"
    )

    if st.button(
        "✅ Verify SMS OTP",
        key="sms_verify_button",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            sms_phone,
            sms_otp
        )

        if success:

            st.session_state.sms_verified = True

            st.success(
                f"🎉 {message}"
            )

            st.balloons()

        else:

            st.error(
                f"❌ {message}"
            )


# ============================================================
# WHATSAPP VERIFICATION
# ============================================================

elif st.session_state.page == "WhatsApp":

    st.header("🟢 WhatsApp Verification")

    st.write(
        "Send a secure six-digit OTP through WhatsApp."
    )

    st.warning(
        "WhatsApp OTP requires WhatsApp to be enabled "
        "and configured in your Twilio Verify Service."
    )

    st.divider()

    whatsapp_phone = st.text_input(
        "WhatsApp Number",
        placeholder="+919876543210",
        key="whatsapp_phone_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_whatsapp_button = st.button(
            "💬 Send WhatsApp OTP",
            key="whatsapp_send_button",
            use_container_width=True
        )

    with col2:

        resend_whatsapp_button = st.button(
            "🔄 Resend WhatsApp OTP",
            key="whatsapp_resend_button",
            use_container_width=True
        )

    if (
        send_whatsapp_button
        or resend_whatsapp_button
    ):

        success, message = send_twilio_otp(
            whatsapp_phone,
            "whatsapp"
        )

        if success:

            st.success(
                f"✅ {message}"
            )

        else:

            st.error(
                f"❌ {message}"
            )

    st.write("")

    whatsapp_otp = st.text_input(
        "Enter WhatsApp OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="whatsapp_otp_input"
    )

    if st.button(
        "✅ Verify WhatsApp OTP",
        key="whatsapp_verify_button",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            whatsapp_phone,
            whatsapp_otp
        )

        if success:

            st.session_state.whatsapp_verified = True

            st.success(
                f"🎉 {message}"
            )

            st.balloons()

        else:

            st.error(
                f"❌ {message}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🔐 PragyanAI • Secure OTP Verification"
)

st.caption(
    "Email • SMS • WhatsApp • Powered by Streamlit"
)
