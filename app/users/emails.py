from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verify_email(to, name, verify_url, verify_code):
    """Send an email to a user to verify their email address"""
    mail_template = "emails/email_verify_email.html"
    subject = "CavingLog - Verify your email"
    html_message = render_to_string(
        mail_template,
        context={
            "name": name,
            "verify_url": verify_url,
            "verify_code": verify_code,
        },
    )
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_FROM

    send_mail(
        subject,
        plain_message,
        from_email,
        [to],
        html_message=html_message,
    )
