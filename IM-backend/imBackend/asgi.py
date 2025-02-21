"""
ASGI config for imBackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
#以下配置socket的代码参考了demo仓库的代码
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from .consumer import IMConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imBackend.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter([
           path('ws/', IMConsumer.as_asgi()),
        ])
    ),
})
