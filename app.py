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
    page_title="PragyanAI | Secure OTP",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background:
            linear-gradient(
                135deg,
                #f8fafc 0%,
                #eef2ff 45%,
                #f8fafc 100%
            );
    }

    /* Hide default menu/footer */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* Header */
    .top-header {
        background:
            linear-gradient(
                135deg,
                #111827,
                #3730a3
            );
        padding: 32px 25px;
        border-radius: 22px;
        color: white;
        text-align: center;
        box-shadow:
            0 12px 30px rgba(31, 41, 55, 0.18);
        margin-bottom: 25px;
    }

    .top-header h1 {
        font-size: 42px;
        font-weight: 800;
        margin: 0;
    }

    .top-header p {
        font-size: 17px;
        margin-top: 8px;
        opacity: 0.88;
    }

    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.96);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #e5e7eb;
        box-shadow:
            0 8px 25px rgba(15, 23, 42, 0.07);
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 24px;
        font-weight: 750;
        color: #111827;
        margin-bottom: 8px;
    }

    .card-description {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 18px;
    }

    /* Status cards */
    .status-card {
        background: white;
        padding: 18px;
        border-radius: 17px;
        border: 1px solid #e5e7eb;
        text-align: center;
        box-shadow:
            0 5px 18px rgba(15, 23, 42, 0.06);
    }

    .status-icon {
        font-size: 30px;
    }

    .status-title {
        font-weight: 700;
        margin-top: 5px;
    }

    .status-text {
        color: #6b7280;
        font-size: 13px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #111827,
                #1e1b4b
            );
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 12px;
        min-height: 45px;
        font-weight: 700;
        border: 0;
    }

    /* Footer */
    .custom-footer {
        margin-top: 35px;
        padding: 25px;
        text-align: center;
        background: #111827;
        color: white;
        border-radius: 20px;
    }

    .custom-footer small {
        color: #cbd5e1;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;">
            <div style="font-size:55px;">🔐</div>
            <h2>PragyanAI</h2>
            <p>OTP Security Center</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### 📡 Available Channels")

    st.write("📧 Email OTP")
    st.write("📱 SMS OTP")
    st.write("🟢 WhatsApp OTP")

    st.divider()

    st.markdown("### 🛡️ Security")

    st.write("🔒 Secure API credentials")
    st.write("⏱️ OTP expiration")
    st.write("🔐 Hashed Email OTP")
    st.write("☁️ Streamlit Secrets")

    st.divider()

    st.caption(
        "PragyanAI Secure Verification"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="top-header">

        <h1>🔐 PragyanAI</h1>

        <p>
            Secure Multi-Channel OTP Verification Platform
        </p>

        <div>
            📧 Email &nbsp;&nbsp;|&nbsp;&nbsp;
            📱 SMS &nbsp;&nbsp;|&nbsp;&nbsp;
            🟢 WhatsApp
        </div>

    </div>
    """,
    unsafe_allow_html=True
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


missing_secrets = [
    secret
    for secret in required_secrets
    if secret not in st.secrets
]


if missing_secrets:

    st.error(
        "❌ Some Streamlit Secrets are missing."
    )

    st.write(
        "Missing secret names:"
    )

    for secret in missing_secrets:

        st.write(
            f"- `{secret}`"
        )

    st.info(
        "Go to Streamlit Cloud → Settings → Secrets "
        "and add the missing names."
    )

    st.stop()


EMAIL_ADDRESS = st.secrets[
    "EMAIL_ADDRESS"
]

EMAIL_APP_PASSWORD = st.secrets[
    "EMAIL_APP_PASSWORD"
]

TWILIO_ACCOUNT_SID = st.secrets[
    "TWILIO_ACCOUNT_SID"
]

TWILIO_AUTH_TOKEN = st.secrets[
    "TWILIO_AUTH_TOKEN"
]

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
# SESSION STATE
# ============================================================

default_state = {

    "email_hash": None,
    "email_created": None,
    "email_verified": False,

    "sms_verified": False,

    "whatsapp_verified": False
}


for key, value in default_state.items():

    if key not in st.session_state:

        st.session_state[key] = value


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

    pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    return re.fullmatch(
        pattern,
        email or ""
    ) is not None


def valid_phone(phone):

    pattern = (
        r"^\+[1-9]\d{7,14}$"
    )

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
# EMAIL OTP
# ============================================================

def send_email_otp(email):

    if not email:

        return False, (
            "❌ Please enter your email address."
        )

    if not valid_email(email):

        return False, (
            "❌ Please enter a valid email address."
        )

    try:

        otp = generate_otp()

        message = EmailMessage()

        message["Subject"] = (
            "PragyanAI - Verification Code"
        )

        message["From"] = EMAIL_ADDRESS

        message["To"] = email

        message.set_content(
            f"""
Hello,

Your PragyanAI verification code is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this code with anyone.

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

        st.session_state.email_hash = (
            hash_otp(otp)
        )

        st.session_state.email_created = (
            time.time()
        )

        st.session_state.email_verified = False

        return True, (
            "✅ Email OTP sent successfully."
        )

    except Exception as error:

        return False, (
            f"❌ Email error: {error}"
        )


def verify_email_otp(otp):

    if not otp:

        return False, (
            "❌ Please enter the Email OTP."
        )

    if (
        not otp.isdigit()
        or len(otp) != 6
    ):

        return False, (
            "❌ OTP must contain exactly 6 digits."
        )

    if st.session_state.email_hash is None:

        return False, (
            "❌ Please send an Email OTP first."
        )

    if otp_expired(
        st.session_state.email_created
    ):

        st.session_state.email_hash = None

        st.session_state.email_created = None

        return False, (
            "⏰ OTP expired. Please request a new OTP."
        )

    if (
        hash_otp(otp)
        == st.session_state.email_hash
    ):

        st.session_state.email_verified = True

        st.session_state.email_hash = None

        st.session_state.email_created = None

        return True, (
            "🎉 Email verified successfully!"
        )

    return False, (
        "❌ Incorrect Email OTP."
    )


# ============================================================
# TWILIO OTP
# ============================================================

def send_twilio_otp(phone, channel):

    if not phone:

        return False, (
            "❌ Please enter your phone number."
        )

    if not valid_phone(phone):

        return False, (
            "❌ Use international format, "
            "for example +919876543210."
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

        return True, (
            f"✅ {channel.upper()} OTP sent successfully. "
            f"Status: {verification.status}"
        )

    except Exception as error:

        return False, (
            f"❌ {channel.upper()} error: {error}"
        )


def verify_twilio_otp(
    phone,
    otp
):

    if not phone:

        return False, (
            "❌ Please enter your phone number."
        )

    if not valid_phone(phone):

        return False, (
            "❌ Use international format, "
            "for example +919876543210."
        )

    if not otp:

        return False, (
            "❌ Please enter the OTP."
        )

    if (
        not otp.isdigit()
        or len(otp) != 6
    ):

        return False, (
            "❌ OTP must contain exactly 6 digits."
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

            return True, (
                "🎉 OTP verified successfully!"
            )

        return False, (
            "❌ Invalid or expired OTP."
        )

    except Exception as error:

        return False, (
            f"❌ Verification error: {error}"
        )


# ============================================================
# STATUS DASHBOARD
# ============================================================

st.markdown(
    "### 📊 Verification Overview"
)

col1, col2, col3 = st.columns(3)


with col1:

    if st.session_state.email_verified:

        icon = "🟢"
        status = "Verified"

    else:

        icon = "⚪"
        status = "Not Verified"

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-icon">📧</div>
            <div class="status-title">
                Email
            </div>
            <div class="status-text">
                {icon} {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    if st.session_state.sms_verified:

        icon = "🟢"
        status = "Verified"

    else:

        icon = "⚪"
        status = "Not Verified"

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-icon">📱</div>
            <div class="status-title">
                SMS
            </div>
            <div class="status-text">
                {icon} {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    if st.session_state.whatsapp_verified:

        icon = "🟢"
        status = "Verified"

    else:

        icon = "⚪"
        status = "Not Verified"

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-icon">🟢</div>
            <div class="status-title">
                WhatsApp
            </div>
            <div class="status-text">
                {icon} {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# ============================================================
# EMAIL SECTION
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="card-title">
            📧 Email Verification
        </div>

        <div class="card-description">
            Verify your email address using a secure
            six-digit OTP.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

email = st.text_input(
    "Email Address",
    placeholder="example@gmail.com",
    key="email_address"
)


email_col1, email_col2 = st.columns(2)


with email_col1:

    email_send = st.button(
        "📨 Send Email OTP",
        key="email_send",
        use_container_width=True
    )


with email_col2:

    email_resend = st.button(
        "🔄 Resend Email OTP",
        key="email_resend",
        use_container_width=True
    )


if email_send or email_resend:

    success, message = send_email_otp(
        email
    )

    if success:

        st.success(message)

    else:

        st.error(message)


email_otp = st.text_input(
    "Enter Email OTP",
    placeholder="Enter 6-digit code",
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


st.divider()


# ============================================================
# SMS SECTION
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="card-title">
            📱 SMS Verification
        </div>

        <div class="card-description">
            Receive a verification code directly
            on your mobile phone.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


sms_phone = st.text_input(
    "Mobile Number",
    placeholder="+919876543210",
    key="sms_phone"
)


sms_col1, sms_col2 = st.columns(2)


with sms_col1:

    sms_send = st.button(
        "📨 Send SMS OTP",
        key="sms_send",
        use_container_width=True
    )


with sms_col2:

    sms_resend = st.button(
        "🔄 Resend SMS OTP",
        key="sms_resend",
        use_container_width=True
    )


if sms_send or sms_resend:

    success, message = send_twilio_otp(
        sms_phone,
        "sms"
    )

    if success:

        st.success(message)

    else:

        st.error(message)


sms_otp = st.text_input(
    "Enter SMS OTP",
    placeholder="Enter 6-digit code",
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
        sms_phone,
        sms_otp
    )

    if success:

        st.session_state.sms_verified = True

        st.success(message)

        st.balloons()

    else:

        st.error(message)


st.divider()


# ============================================================
# WHATSAPP SECTION
# ============================================================

st.markdown(
    """
    <div class="card">

        <div class="card-title">
            🟢 WhatsApp Verification
        </div>

        <div class="card-description">
            Send a verification code through WhatsApp
            using your configured Twilio Verify service.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.info(
    "ℹ️ WhatsApp OTP requires WhatsApp to be enabled "
    "and configured in your Twilio Verify Service."
)


whatsapp_phone = st.text_input(
    "WhatsApp Number",
    placeholder="+919876543210",
    key="whatsapp_phone"
)


whatsapp_col1, whatsapp_col2 = st.columns(2)


with whatsapp_col1:

    whatsapp_send = st.button(
        "💬 Send WhatsApp OTP",
        key="whatsapp_send",
        use_container_width=True
    )


with whatsapp_col2:

    whatsapp_resend = st.button(
        "🔄 Resend WhatsApp OTP",
        key="whatsapp_resend",
        use_container_width=True
    )


if whatsapp_send or whatsapp_resend:

    success, message = send_twilio_otp(
        whatsapp_phone,
        "whatsapp"
    )

    if success:

        st.success(message)

    else:

        st.error(message)


whatsapp_otp = st.text_input(
    "Enter WhatsApp OTP",
    placeholder="Enter 6-digit code",
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
        whatsapp_phone,
        whatsapp_otp
    )

    if success:

        st.session_state.whatsapp_verified = True

        st.success(message)

        st.balloons()

    else:

        st.error(message)


# ============================================================
# FINAL STATUS
# ============================================================

st.divider()

all_verified = (
    st.session_state.email_verified
    and st.session_state.sms_verified
    and st.session_state.whatsapp_verified
)


if all_verified:

    st.success(
        "🎉 All three verification channels "
        "have been successfully verified!"
    )

else:

    st.info(
        "🔐 Complete the required verification "
        "channels above."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="custom-footer">

        <div style="font-size:24px;">
            🔐 PragyanAI
        </div>

        <div style="margin-top:8px;">
            Secure Multi-Channel OTP Verification
        </div>

        <br>

        <small>
            📧 Email &nbsp; • &nbsp;
            📱 SMS &nbsp; • &nbsp;
            🟢 WhatsApp
        </small>

        <br><br>

        <small>
            API credentials are securely loaded
            from Streamlit Secrets.
        </small>

    </div>
    """,
    unsafe_allow_html=True
)
