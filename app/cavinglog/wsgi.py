"""
WSGI config for caves.app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
import os  # pragma: no cover

from django.core.wsgi import get_wsgi_application  # pragma: no cover

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "cavinglog.settings"
)  # pragma: no cover  # noqa: E501
application = get_wsgi_application()  # pragma: no cover
