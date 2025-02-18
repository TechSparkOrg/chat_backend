# chat_backend/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import chat.routing
from chat.middleware import TokenAuthMiddleware
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_backend.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
