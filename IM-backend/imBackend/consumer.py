import json
from channels.generic.websocket import AsyncWebsocketConsumer

import datetime
import hashlib
import hmac
import time
import json
import base64
from typing import Optional
from utils.utils_jwt import generate_jwt_token, check_jwt_token

connected_channels = set()

class IMConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        auth_header_value = self.scope['query_string'].decode('utf-8').split('=', 1)[1]
        if not auth_header_value:
            await self.close(code=401)
            return
        
        decoded_token = check_jwt_token(auth_header_value)
        if decoded_token is None:
            await self.close(code=401)
            return

        # 从解析结果中获取用户名和用户ID
        self.user_name = decoded_token.get('userName')
        self.user_id = decoded_token.get('userId')
        connected_channels.add(self.user_id)
        await self.channel_layer.group_add(str(self.user_id), self.channel_name)
        await self.accept()

    # 当 WebSocket 连接关闭时调用
    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, 'user_id'):
            connected_channels.discard(self.user_id)
            await self.channel_layer.group_discard(str(self.user_id), self.channel_name)

    async def receive_message(self, event) -> None:
        return_data = event.get('data', {})
        await self.send(text_data=json.dumps({'type': 'receive_message', 'message': return_data}))

    async def receive_friend_application(self, event) -> None:
        return_data = event.get('data', {})
        await self.send(text_data=json.dumps({'type': 'receive_friend_application', 'message': return_data}))

    async def friend_application_agreed(self, event) -> None:
        return_data = event.get('data', {})
        await self.send(text_data=json.dumps({'type': 'friend_application_agreed', 'message': return_data}))

    async def invited_to_conversation(self, event) -> None:
        return_data = event.get('data', {})
        await self.send(text_data=json.dumps({'type': 'invited_to_conversation', 'message': return_data}))

    async def receive_conversation_application(self, event) -> None:
        return_data = event.get('data', {})
        await self.send(text_data=json.dumps({'type': 'receive_conversation_application', 'message': return_data}))

        