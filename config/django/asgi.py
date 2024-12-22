"""ASGI config for caves.app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os  # pragma: no cover

from django.core.asgi import get_asgi_application  # pragma: no cover

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "config.django.settings.base"
)  # pragma: no cover # noqa: E501
application = get_asgi_application()  # pragma: no cover
