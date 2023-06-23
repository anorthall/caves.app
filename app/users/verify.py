from django.conf import settings
from django.core.exceptions import ValidationError
from itsdangerous import URLSafeTimedSerializer

# Thanks to https://realpython.com/handling-email-confirmation-in-flask/


def generate_token(user_pk, email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps([user_pk, email], salt="verify-email")


def verify_token(token, expiration=86400):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        user_pk, email = serializer.loads(
            token,
            salt="verify-email",
            max_age=expiration,
        )
    except Exception:
        raise ValidationError("Email verification code is not valid or has expired.")
    return user_pk, email
