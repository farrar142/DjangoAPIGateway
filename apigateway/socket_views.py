# # chat/consumers.py
# import json
# import websockets
# from websockets.client import ClientConnection
# from websockets.legacy.client import Connect, WebSocketClientProtocol
# from pprint import pprint
# from unidecode import unidecode
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.layers import InMemoryChannelLayer


# class AsyncWebsocketConsumerImpl(AsyncWebsocketConsumer):
#     channel_layer: InMemoryChannelLayer


# async def accept(websocket, path):
#     while True:
#         data = await websocket.recv()  # 클라이언트로부터 메시지를 대기한다.
#         print("receive : " + data)
#         await websocket.send("ws_srv send data = " + data)


# class APIConsumer(AsyncWebsocketConsumerImpl):
#     async def connect(self):
#         pprint(self.scope['path'])
#         print(self.scope['user'])
#         self.room_group_name = self.scope['path']
#         # ClientConnection(b'webrtcbackend.honeycombpizza.link/ws/dawd/4'
#         await self.channel_layer.group_add(
#             unidecode(self.room_group_name),
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat',
#                 'data': text_data_json,
#             }
#         )

#     # Receive message from room group
#     async def chat(self, event):
#         data = event['data']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'data': data,
#         }))
