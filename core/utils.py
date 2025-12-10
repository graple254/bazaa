import random
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def generate_verification_code():
    """Generate a 6-digit random verification code."""
    return str(random.randint(100000, 999999))


def send_verification_email(email, code, html_content=None):
    """
    Generic email sender for both verification and reset.
    - If html_content is provided → use it.
    - If html_content is None → build default verification HTML.
    """

    # Split API key
    api_key = (
        "xkeysib"
        "-65f87098e4405520b41fc9ac188abfbabd646ea947a9045a9ccde4c94795bdc8"
        "-aagjFFbYWsUuLbyS"
    )

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # Determine email subject + HTML based on usage
    if html_content is None:
        # Normal verification flow
        subject = "Your Bazaa Digital Verification Code"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Your Verification Code</h2>
                <p>Use the code below to complete your signup on <strong>Bazaa Digital</strong>.</p>
                <h1 style="letter-spacing: 4px;">{code}</h1>
                <p>If you did not request this, ignore this email.</p>
            </body>
        </html>
        """
    else:
        # Password reset flow
        subject = "Reset Your Password - Bazaa Digital"
        # html_content was already provided by reset function

    sender = {
        "email": "noreply@bazaa.digital",
        "name": "Bazaa.Digital"
    }

    email_obj = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email}],
        html_content=html_content,
        subject=subject,
        sender=sender
    )

    try:
        api_instance.send_transac_email(email_obj)
        print("Email sent successfully.")
        return True
    except ApiException as e:
        print(f"Brevo email send failed: {str(e)}")
        return False


def send_password_reset_email(email, link):
    html_contents = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Reset Your Password</h2>
            <p>Click the button below to reset your password:</p>
            <p><a href="{link}" style="padding:10px 20px; background:#4CAF50; color:white; text-decoration:none; border-radius:4px;">Reset Password</a></p>
            <p>This link expires in 15 minutes.</p>
            <p>If you did not request this, you can safely ignore this email.</p>
        </body>
    </html>
    """

    # Trick: we pass `code=None` but override via html_contents
    send_verification_email(email, code=None, html_content=html_contents)
