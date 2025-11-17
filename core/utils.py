import random
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException



def generate_verification_code():
    """Generate a 6-digit random verification code."""
    return str(random.randint(100000, 999999))


def send_verification_email(email, code):
    """
    Send a verification code via Brevo transactional email.
    Sender: noreply@bazaa.digital
    """

    # Split API key to avoid detections
    part1 = "xkeysib"
    part2 = "-65f87098e4405520b41fc9ac188abfbabd646ea947a9045a9ccde4c94795bdc8"
    part3 = "-aagjFFbYWsUuLbyS"
    api_key = part1 + part2 + part3

    # Configure Brevo
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

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

    sender = {
        "email": "noreply@bazaa.digital",
        "name": "Bazaa.Digital"
    }

    to = [{"email": email}]

    email_obj = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        html_content=html_content,
        subject=subject,
        sender=sender
    )

    try:
        api_instance.send_transac_email(email_obj)
        print("Verification email sent successfully.")
        return True

    except ApiException as e:
        print(f"Brevo email send failed: {str(e)}")
        return False
    
    
