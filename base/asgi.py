import os
import django

# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter, get_default_application
# from channels.security.websocket import OriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path, path

# from apigateway.socket_auth import TokenAuthMiddleware
# from .routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings.prod")
print("asgi called")
# application = get_default_application()
application = get_asgi_application()
# application = ProtocolTypeRouter(
#     {
#         "http": get_asgi_application(),
#         "websocket": OriginValidator(
#             TokenAuthMiddleware(URLRouter(websocket_urlpatterns)),
#             ["*"],
#         ),
#     }
# )
