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
# CUSTOM CSS
# Only styling here - NO HTML UI components
# ============================================================

st.markdown(
    """
    <style>

    /* Main application background */
    .stApp {
        background-color: #f5f7fb;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        min-height: 46px;
        border-radius: 10px;
        border: 1px solid #374151;
        background-color: #1f2937;
        color: white;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #374151;
        border-color: #6366f1;
    }

    /* Main buttons */
    .stButton button {
        min-height: 45px;
        border-radius: 10px;
        font-weight: 700;
    }

    /* Metric styling */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 15px;
    }

    /* Input boxes */
    div[data-baseweb="input"] {
        border-radius: 10px;
    }

    /* Hide Streamlit footer */
    footer {
        visibility: hidden;
    }

    /* Hide menu */
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
        "Please add the following values in:"
    )

    st.code(
        "Streamlit Cloud → Manage app → Settings → Secrets"
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
    """
    Generate a secure 6-digit OTP.
    """

    return f"{random.SystemRandom().randint(0, 999999):06d}"


def hash_otp(otp):
    """
    Hash OTP before storing it in session state.
    """

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def valid_email(email):
    """
    Basic email validation.
    """

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.fullmatch(
        pattern,
        email or ""
    ) is not None


def valid_phone(phone):
    """
    International phone number validation.

    Example:
    +919876543210
    """

    pattern = r"^\+[1-9]\d{7,14}$"

    return re.fullmatch(
        pattern,
        phone or ""
    ) is not None


def otp_expired(created_time):
    """
    Email OTP validity:
    5 minutes.
    """

    if created_time is None:
        return True

    return (
        time.time() - created_time
    ) > 300


# ============================================================
# EMAIL OTP
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
# TWILIO SEND OTP
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
# TWILIO VERIFY OTP
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
# MAIN HEADER
# ============================================================

st.title("🔐 PragyanAI")

st.subheader(
    "Secure Multi-Channel OTP Verification Platform"
)

st.caption(
    "Verify users securely through Email, SMS and WhatsApp."
)

st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.header("🏠 Security Dashboard")

    st.write(
        "Manage OTP verification from one secure platform."
    )

    st.write("")

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    st.subheader("📊 Verification Status")

    col1, col2, col3 = st.columns(3)

    with col1:

        email_status = (
            "Verified"
            if st.session_state.email_verified
            else "Not Verified"
        )

        st.metric(
            "📧 Email",
            email_status
        )

    with col2:

        sms_status = (
            "Verified"
            if st.session_state.sms_verified
            else "Not Verified"
        )

        st.metric(
            "📱 SMS",
            sms_status
        )

    with col3:

        whatsapp_status = (
            "Verified"
            if st.session_state.whatsapp_verified
            else "Not Verified"
        )

        st.metric(
            "🟢 WhatsApp",
            whatsapp_status
        )

    st.divider()

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.subheader("🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "📧 Email Verification",
            key="quick_email",
            use_container_width=True
        ):

            st.session_state.page = "Email"

            st.rerun()

    with col2:

        if st.button(
            "📱 SMS Verification",
            key="quick_sms",
            use_container_width=True
        ):

            st.session_state.page = "SMS"

            st.rerun()

    with col3:

        if st.button(
            "🟢 WhatsApp Verification",
            key="quick_whatsapp",
            use_container_width=True
        ):

            st.session_state.page = "WhatsApp"

            st.rerun()

    st.divider()

    st.info(
        "💡 Select a channel from the sidebar to start verification."
    )


# ============================================================
# EMAIL PAGE
# ============================================================

elif st.session_state.page == "Email":

    st.header("📧 Email Verification")

    st.caption(
        "Send a six-digit OTP to an email address and verify it."
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
# SMS PAGE
# ============================================================

elif st.session_state.page == "SMS":

    st.header("📱 SMS Verification")

    st.caption(
        "Send a six-digit OTP to a mobile number."
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
# WHATSAPP PAGE
# ============================================================

elif st.session_state.page == "WhatsApp":

    st.header("🟢 WhatsApp Verification")

    st.caption(
        "Send a six-digit OTP through WhatsApp."
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
