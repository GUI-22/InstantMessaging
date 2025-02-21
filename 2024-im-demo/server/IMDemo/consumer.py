import json
from channels.generic.websocket import AsyncWebsocketConsumer

import datetime
import hashlib
import hmac
import time
import json
import base64
from typing import Optional

# c.f. https://thuse-course.github.io/course-index/basic/jwt/#jwt
# !Important! Change this to your own salt, better randomly generated!"
JWT_SALT = b'v\xea\xece\xb5\x92\x135\x92\x14\x89\xaa\xb7\xc2\xbeb<\x7f\x85\xdb@z\x8aF\xaa\x06\x81\x84\xff\xc2\xef3'
EXPIRE_IN_SECONDS = 60 * 60 * 24 * 1  # 1 day
ALT_CHARS = "-_".encode("utf-8")
BlackList = set()


def b64url_encode(s):
    if isinstance(s, str):
        return base64.b64encode(s.encode("utf-8"), altchars=ALT_CHARS).decode("utf-8")
    else:
        return base64.b64encode(s, altchars=ALT_CHARS).decode("utf-8")

def b64url_decode(s: str, decode_to_str=True):
    if decode_to_str:
        return base64.b64decode(s, altchars=ALT_CHARS).decode("utf-8")
    else:
        return base64.b64decode(s, altchars=ALT_CHARS)


def generate_jwt_token(username: str, userId):
    # * header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    # dump to str. remove `\n` and space after `:`
    header_str = json.dumps(header, separators=(",", ":"))
    # use base64url to encode, instead of base64
    header_b64 = b64url_encode(header_str)
    
    # * payload
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + EXPIRE_IN_SECONDS,
        "data": {
            "userName": username,
            "userId": userId
            # And more data for your own usage
        }
    }
    payload_str = json.dumps(payload, separators=(",", ":"))
    payload_b64 = b64url_encode(payload_str)
    
    # * signature
    signature_raw = header_b64 + "." + payload_b64
    signature = hmac.new(JWT_SALT, signature_raw.encode("utf-8"), digestmod=hashlib.sha256).digest()
    signature_b64 = b64url_encode(signature)
    
    return header_b64 + "." + payload_b64 + "." + signature_b64

with open("/root/SE/IM/quick_test.py", "w") as file:
    file.write(generate_jwt_token("cc", 3))


def check_jwt_token(token: str) -> Optional[dict]:
    # * Split token
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except:
        return None
    if token in BlackList:
        return None
    payload_str = b64url_decode(payload_b64)
    
    # * Check signature
    signature_str_check = header_b64 + "." + payload_b64
    signature_check = hmac.new(JWT_SALT, signature_str_check.encode("utf-8"), digestmod=hashlib.sha256).digest()
    signature_b64_check = b64url_encode(signature_check)
    
    if signature_b64_check != signature_b64:
        print("real jwt:\n", signature_b64_check)
        print("frontend jwt:\n", signature_b64)
        print("different")
        return None
    
    # Check expire
    payload = json.loads(payload_str)
    if payload["exp"] < time.time():
        return None
    
    return payload["data"]


class IMDemoConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        # 从 WebSocket 连接的 header 中获取 JWT
        print("***")
        print(self.scope)
        print("***")
        # 遍历 headers 列表，找到 Authorization 头部的值
        auth_header_value = None
        for header_key, header_value in self.scope.get('headers', []):
            if header_key == b'authorization':
                auth_header_value = header_value
                break
        if not auth_header_value:
            # 如果没有提供 JWT，则拒绝连接并发送 401 Unauthorized 响应
            await self.close(code=401)
            return
        
        # 解析 JWT
        decoded_token = check_jwt_token(auth_header_value.decode('utf-8'))
        print("###")
        print(decoded_token)
        print("###")
        if decoded_token is None:
            # 如果 JWT 无效，则拒绝连接并发送 401 Unauthorized 响应
            await self.close(code=401)
            return

        # 从解析结果中获取用户名和用户ID
        self.user_name = decoded_token.get('userName')
        self.user_id = decoded_token.get('userId')

        # 将当前 WebSocket 连接添加到一个全体用户组中
        await self.channel_layer.group_add(self.user_name, self.channel_name)
        
        # 发送 200 OK 响应
        await self.accept()
        
    # # 当客户端尝试建立 WebSocket 连接时调用
    # async def connect(self) -> None:
    #     # 从查询字符串中提取用户名
    #     self.username: str = self.scope['query_string'].decode('utf-8').split('=')[1]

    #     # 将当前 WebSocket 连接添加到一个全体用户组中
    #     # 这样可以确保发给这个组的所有消息都会被转发给目前连接的所有客户端
    #     await self.channel_layer.group_add(self.username, self.channel_name)

    #     # 接受 WebSocket 连接
    #     await self.accept()

    # 当 WebSocket 连接关闭时调用
    async def disconnect(self, close_code: int) -> None:
        # 将当前 WebSocket 从其所在的组中移除
        # 如果成功解析了 JWT 并获取了用户名，则执行下面的操作
        if hasattr(self, 'userName'):
            # 将当前 WebSocket 从其所在的组中移除
            await self.channel_layer.group_discard(self.user_name, self.channel_name)

    # 向指定用户组发送 notification
    async def notify(self, event) -> None:
        await self.send(text_data=json.dumps({'type': 'notify'}))

        