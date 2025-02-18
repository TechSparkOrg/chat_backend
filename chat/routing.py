# chat/routing.py
import logging
import chat.consumers  # Import the consumers module

# Print available attributes to help debug import issues
logger = logging.getLogger(__name__)
logger.info(f"Attributes in chat.consumers: {dir(chat.consumers)}")

from django.urls import re_path
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<uuid>[\w-]+)/$', ChatConsumer.as_asgi()),
]
