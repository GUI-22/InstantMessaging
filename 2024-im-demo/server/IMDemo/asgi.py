"""
ASGI config for IMDemo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from .consumer import IMDemoConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IMDemo.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
           path('ws/', IMDemoConsumer.as_asgi()),
        ])
    ),
})