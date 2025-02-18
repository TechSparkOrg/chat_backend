# chat/middleware.py
import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    """
    Custom middleware that takes a token from the query string and authenticates via DRF Token.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Extract the token from the query string (e.g., ?token=abcd1234)
        query_string = scope.get("query_string", b"").decode()
        qs = parse_qs(query_string)
        token_key = qs.get("token", [None])[0]
        
        if token_key:
            user = await get_user(token_key)
            logger.info(f"Authenticated user via token: {user}")
        else:
            user = AnonymousUser()
            logger.info("No token provided; setting user as AnonymousUser")
        
        # Attach the user to the scope
        scope["user"] = user
        
        # Call the inner application with the updated scope.
        return await self.inner(scope, receive, send)
