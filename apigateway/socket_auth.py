# from channels.auth import AuthMiddlewareStack


# class TokenAuthMiddleware:
#     """
#     Token authorization middleware for Django Channels 2
#     """

#     def __init__(self, inner):
#         self.inner = inner

#     def __call__(self, scope, receive, send, *args, **kwargs):
#         headers = dict(scope['headers'])
#         from django.contrib.auth.models import AnonymousUser
#         from rest_framework.authtoken.models import Token
#         query_string: bytes = scope['query_string']
#         qs = query_string.decode().split("&")
#         for q in qs:
#             key, val = q.split("=")
#             if key == "token":
#                 print("user set", val)
#                 scope["user"] = val
#         return self.inner(scope, receive, send)
