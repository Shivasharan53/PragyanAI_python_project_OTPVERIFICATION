import streamlit as st
import smtplib
import random
import time
import hashlib
import re

from email.message import EmailMessage
from twilio.rest import Client


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="PragyanAI OTP Security",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background: #f4f7fb;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #111827 0%,
            #1e1b4b 100%
        );
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: white !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 48px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(255,255,255,0.07);
        color: white;
        font-weight: 600;
        text-align: left;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.16);
        border-color: rgba(255,255,255,0.35);
        color: white;
    }

    /* Main header */
    .main-header {
        background: linear-gradient(
            135deg,
            #111827,
            #312e81
        );
        border-radius: 20px;
        padding: 30px;
        color: white;
        box-shadow: 0 10px 30px rgba(15,23,42,0.12);
        margin-bottom: 25px;
    }

    .main-header-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .main-header-subtitle {
        font-size: 16px;
        color: #dbeafe;
    }

    /* Cards */
    .professional-card {
        background: white;
        border-radius: 18px;
        padding: 24px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 7px 25px rgba(15,23,42,0.06);
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 22px;
        font-weight: 750;
        color: #111827;
    }

    .card-description {
        color: #64748b;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    /* Status cards */
    .status-box {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 5px 18px rgba(15,23,42,0.05);
    }

    .status-icon {
        font-size: 30px;
    }

    .status-name {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
        margin-top: 6px;
    }

    .status-value {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
    }

    /* Buttons */
    div.stButton > button {
        min-height: 45px;
        border-radius: 10px;
        font-weight: 700;
    }

    /* Footer */
    .footer-box {
        margin-top: 35px;
        background: #111827;
        color: white;
        border-radius: 18px;
        padding: 22px;
        text-align: center;
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

    st.markdown(
        "## 🔐 PragyanAI"
    )

    st.caption(
        "Secure OTP Verification"
    )

    st.divider()

    st.markdown(
        "### Navigation"
    )

    if st.button(
        "🏠  Dashboard",
        key="nav_dashboard"
    ):
        st.session_state.page = "Dashboard"
        st.rerun()

    if st.button(
        "📧  Email Verification",
        key="nav_email"
    ):
        st.session_state.page = "Email"
        st.rerun()

    if st.button(
        "📱  SMS Verification",
        key="nav_sms"
    ):
        st.session_state.page = "SMS"
        st.rerun()

    if st.button(
        "🟢  WhatsApp Verification",
        key="nav_whatsapp"
    ):
        st.session_state.page = "WhatsApp"
        st.rerun()

    st.divider()

    st.markdown(
        "### Security"
    )

    st.write("🔒 Secure credentials")
    st.write("⏱️ OTP expiry")
    st.write("🔐 OTP hashing")
    st.write("☁️ Streamlit Secrets")

    st.divider()

    st.caption(
        "PragyanAI Security Platform"
    )

    st.caption(
        "Email • SMS • WhatsApp"
    )


# ============================================================
# LOAD SECRETS
# ============================================================

required_secrets = [
    "EMAIL_ADDRESS",
    "EMAIL_APP_PASSWORD",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_VERIFY_SERVICE_SID"
]

missing_secrets = []

for secret in required_secrets:

    if secret not in st.secrets:
        missing_secrets.append(secret)


if missing_secrets:

    st.error(
        "❌ Streamlit Secrets are not configured."
    )

    st.write(
        "Add these secret names in "
        "Streamlit Cloud → Settings → Secrets:"
    )

    for secret in missing_secrets:
        st.code(secret)

    st.stop()


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


def otp_expired(created):

    if created is None:
        return True

    return (
        time.time() - created
    ) > 300


# ============================================================
# EMAIL OTP FUNCTIONS
# ============================================================

def send_email_otp(email):

    if not email:
        return False, "Please enter your email address."

    if not valid_email(email):
        return False, "Please enter a valid email address."

    try:

        otp = generate_otp()

        message = EmailMessage()

        message["Subject"] = (
            "PragyanAI - Email Verification Code"
        )

        message["From"] = EMAIL_ADDRESS

        message["To"] = email

        message.set_content(
            f"""
Hello,

Your PragyanAI verification code is:

{otp}

This OTP is valid for 5 minutes.

Do not share this code with anyone.

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

        st.session_state.email_hash = hash_otp(otp)

        st.session_state.email_created = time.time()

        st.session_state.email_verified = False

        return True, "Email OTP sent successfully."

    except Exception as error:

        return False, f"Email error: {error}"


def verify_email_otp(otp):

    if not otp:
        return False, "Please enter the Email OTP."

    if not otp.isdigit() or len(otp) != 6:
        return False, "OTP must contain exactly 6 digits."

    if st.session_state.email_hash is None:
        return False, "Please send an Email OTP first."

    if otp_expired(
        st.session_state.email_created
    ):

        st.session_state.email_hash = None
        st.session_state.email_created = None

        return False, "OTP expired. Please request a new OTP."

    if (
        hash_otp(otp)
        == st.session_state.email_hash
    ):

        st.session_state.email_verified = True

        st.session_state.email_hash = None
        st.session_state.email_created = None

        return True, "Email verified successfully."

    return False, "Incorrect Email OTP."


# ============================================================
# TWILIO FUNCTIONS
# ============================================================

def send_twilio_otp(phone, channel):

    if not phone:
        return False, "Please enter your phone number."

    if not valid_phone(phone):

        return (
            False,
            "Use international format, for example "
            "+919876543210"
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
            f"{channel.upper()} error: {error}"
        )


def verify_twilio_otp(phone, otp):

    if not phone:
        return False, "Please enter your phone number."

    if not valid_phone(phone):

        return (
            False,
            "Use international format, for example "
            "+919876543210"
        )

    if not otp:
        return False, "Please enter the OTP."

    if not otp.isdigit() or len(otp) != 6:
        return False, "OTP must contain exactly 6 digits."

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

            return True, "OTP verified successfully."

        return False, "Incorrect or expired OTP."

    except Exception as error:

        return False, f"Verification error: {error}"


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">

        <div class="main-header-title">
            🔐 PragyanAI
        </div>

        <div class="main-header-subtitle">
            Secure Multi-Channel OTP Verification Platform
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.title("🏠 Security Dashboard")

    st.write(
        "Manage and verify users through multiple "
        "secure communication channels."
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:

        email_status = (
            "🟢 Verified"
            if st.session_state.email_verified
            else "⚪ Not Verified"
        )

        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-icon">📧</div>
                <div class="status-name">
                    Email
                </div>
                <div class="status-value">
                    {email_status}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        sms_status = (
            "🟢 Verified"
            if st.session_state.sms_verified
            else "⚪ Not Verified"
        )

        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-icon">📱</div>
                <div class="status-name">
                    SMS
                </div>
                <div class="status-value">
                    {sms_status}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        whatsapp_status = (
            "🟢 Verified"
            if st.session_state.whatsapp_verified
            else "⚪ Not Verified"
        )

        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-icon">🟢</div>
                <div class="status-name">
                    WhatsApp
                </div>
                <div class="status-value">
                    {whatsapp_status}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.write("")

    st.subheader("🚀 Quick Actions")

    quick1, quick2, quick3 = st.columns(3)

    with quick1:

        if st.button(
            "📧 Open Email",
            key="quick_email",
            use_container_width=True
        ):

            st.session_state.page = "Email"
            st.rerun()

    with quick2:

        if st.button(
            "📱 Open SMS",
            key="quick_sms",
            use_container_width=True
        ):

            st.session_state.page = "SMS"
            st.rerun()

    with quick3:

        if st.button(
            "🟢 Open WhatsApp",
            key="quick_whatsapp",
            use_container_width=True
        ):

            st.session_state.page = "WhatsApp"
            st.rerun()

    st.info(
        "💡 Select a verification channel from the "
        "sidebar to begin."
    )


# ============================================================
# EMAIL PAGE
# ============================================================

elif st.session_state.page == "Email":

    st.title("📧 Email Verification")

    st.write(
        "Send and verify a secure six-digit OTP "
        "through email."
    )

    st.markdown(
        '<div class="professional-card">',
        unsafe_allow_html=True
    )

    email = st.text_input(
        "Email Address",
        placeholder="example@gmail.com",
        key="email_address_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_email = st.button(
            "📨 Send OTP",
            key="send_email_button",
            use_container_width=True
        )

    with col2:

        resend_email = st.button(
            "🔄 Resend OTP",
            key="resend_email_button",
            use_container_width=True
        )

    if send_email or resend_email:

        success, message = send_email_otp(
            email
        )

        if success:
            st.success(message)
        else:
            st.error(message)

    email_code = st.text_input(
        "Enter OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="email_code_input"
    )

    if st.button(
        "✅ Verify Email",
        key="verify_email_button",
        use_container_width=True
    ):

        success, message = verify_email_otp(
            email_code
        )

        if success:

            st.success(message)
            st.balloons()

        else:

            st.error(message)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# SMS PAGE
# ============================================================

elif st.session_state.page == "SMS":

    st.title("📱 SMS Verification")

    st.write(
        "Send and verify an OTP through SMS."
    )

    st.markdown(
        '<div class="professional-card">',
        unsafe_allow_html=True
    )

    phone = st.text_input(
        "Mobile Number",
        placeholder="+919876543210",
        key="sms_phone_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_sms = st.button(
            "📨 Send SMS OTP",
            key="send_sms_button",
            use_container_width=True
        )

    with col2:

        resend_sms = st.button(
            "🔄 Resend SMS OTP",
            key="resend_sms_button",
            use_container_width=True
        )

    if send_sms or resend_sms:

        success, message = send_twilio_otp(
            phone,
            "sms"
        )

        if success:
            st.success(message)
        else:
            st.error(message)

    sms_code = st.text_input(
        "Enter SMS OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="sms_code_input"
    )

    if st.button(
        "✅ Verify SMS",
        key="verify_sms_button",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            phone,
            sms_code
        )

        if success:

            st.session_state.sms_verified = True

            st.success(message)
            st.balloons()

        else:

            st.error(message)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# WHATSAPP PAGE
# ============================================================

elif st.session_state.page == "WhatsApp":

    st.title("🟢 WhatsApp Verification")

    st.write(
        "Send and verify an OTP through WhatsApp."
    )

    st.warning(
        "WhatsApp must be enabled and configured "
        "in your Twilio Verify Service."
    )

    st.markdown(
        '<div class="professional-card">',
        unsafe_allow_html=True
    )

    whatsapp_phone = st.text_input(
        "WhatsApp Number",
        placeholder="+919876543210",
        key="whatsapp_phone_input"
    )

    col1, col2 = st.columns(2)

    with col1:

        send_whatsapp = st.button(
            "💬 Send WhatsApp OTP",
            key="send_whatsapp_button",
            use_container_width=True
        )

    with col2:

        resend_whatsapp = st.button(
            "🔄 Resend WhatsApp OTP",
            key="resend_whatsapp_button",
            use_container_width=True
        )

    if send_whatsapp or resend_whatsapp:

        success, message = send_twilio_otp(
            whatsapp_phone,
            "whatsapp"
        )

        if success:
            st.success(message)
        else:
            st.error(message)

    whatsapp_code = st.text_input(
        "Enter WhatsApp OTP",
        placeholder="Enter 6-digit OTP",
        max_chars=6,
        type="password",
        key="whatsapp_code_input"
    )

    if st.button(
        "✅ Verify WhatsApp",
        key="verify_whatsapp_button",
        use_container_width=True
    ):

        success, message = verify_twilio_otp(
            whatsapp_phone,
            whatsapp_code
        )

        if success:

            st.session_state.whatsapp_verified = True

            st.success(message)
            st.balloons()

        else:

            st.error(message)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer-box">

        <div style="font-size:24px;font-weight:700;">
            🔐 PragyanAI
        </div>

        <div style="margin-top:8px;">
            Secure Multi-Channel OTP Verification
        </div>

        <div style="margin-top:12px;color:#cbd5e1;">
            📧 Email &nbsp; • &nbsp;
            📱 SMS &nbsp; • &nbsp;
            🟢 WhatsApp
        </div>

        <div style="margin-top:15px;color:#94a3b8;font-size:13px;">
            Credentials are securely loaded from
            Streamlit Secrets.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)
