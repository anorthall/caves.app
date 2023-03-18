from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verify_email(to, name, verify_url, verify_code):
    """Send an email to a new user to verify their email address"""
    mail_template = "emails/email_verify_new_account.html"
    subject = "Welcome to caves.app - verify your email"
    html_message = render_to_string(
        mail_template,
        context={
            "name": name,
            "verify_url": verify_url,
            "verify_code": verify_code,
        },
    )
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject,
        plain_message,
        from_email,
        [to],
        html_message=html_message,
    )


def send_email_change_verification(to, name, verify_url, verify_code):
    """Send an email to a user to change their email address"""
    mail_template = "emails/email_verify_change.html"
    subject = "Verify your change of email"
    html_message = render_to_string(
        mail_template,
        context={
            "name": name,
            "verify_url": verify_url,
            "verify_code": verify_code,
        },
    )
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject,
        plain_message,
        from_email,
        [to],
        html_message=html_message,
    )


def send_email_change_notification(to, name, new_email):
    """Send an email to a user to notify them of a change of email address"""
    mail_template = "emails/email_notify_change.html"
    subject = "Change of email address requested"
    html_message = render_to_string(
        mail_template,
        context={
            "name": name,
            "old_email": to,
            "new_email": new_email,
        },
    )
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject,
        plain_message,
        from_email,
        [to],
        html_message=html_message,
    )
