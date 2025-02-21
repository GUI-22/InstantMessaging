from django.test import TestCase
import random
from django.test import TestCase, Client
from user.models import User
from friend.models import UserReadFriendChainTime
from message.models import UserReadUserChainTime
from utils.utils_time import get_timestamp
from utils.utils_const import PASSWORD_SALT, PICTURE_STR
import hashlib
from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
import hmac
import time
import json
import base64
import json
from datetime import datetime

from utils.utils_jwt import EXPIRE_IN_SECONDS, JWT_SALT, b64url_encode

# Create your tests here.
class MessageTests(TestCase):
    senderUserName = "Alice"
    senderUserId = 0
    appliedUserName = "Bob"
    appliedUserId = 0
    messageId = 0
    # receiverUserName
    # Initializer
    def setUp(self):
        User.objects.filter(name=self.senderUserName).delete()
        user = User.objects.create(name=self.senderUserName, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.id}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()

        self.senderUserId = user.id
        
        User.objects.filter(name=self.appliedUserName).delete()
        user = User.objects.create(name=self.appliedUserName, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.id}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()
        self.appliedUserId = user.id
        
    # ! Utility functions
    def generate_jwt_token(self, username: str, payload: dict, salt: str):
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
        payload_str = json.dumps(payload, separators=(",", ":"))
        payload_b64 = b64url_encode(payload_str)
        
        # * signature
        signature_str = header_b64 + "." + payload_b64
        signature = hmac.new(salt, signature_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature_b64 = b64url_encode(signature)
        
        return header_b64 + "." + payload_b64 + "." + signature_b64

    
    def generate_header(self, userName: str, userId: int, payload: dict = {}, salt: str = JWT_SALT):
        if len(payload) == 0:
            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + EXPIRE_IN_SECONDS,
                "data": {
                    "userName": userName,
                    "userId": userId
                }
            }
        return {
            "HTTP_AUTHORIZATION": self.generate_jwt_token(userName, payload, salt)
        }
    
    def test_send_message(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.senderUserName, self.senderUserId)
        self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)


        data = {"userId": self.appliedUserId, "senderUserId": self.senderUserId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        conversation_id = res.json()["conversation_id"]
        data = {"conversationId": conversation_id, "message":"hello!", "replyId":-1}
        res = self.client.put('/message/send_message', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_user_chain(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.senderUserName, self.senderUserId)
        self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)


        data = {"userId": self.appliedUserId, "senderUserId": self.senderUserId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        conversation_id = res.json()["conversation_id"]
        data = {"conversationId": conversation_id, "message":"hello!"}
        res = self.client.put('/message/send_message', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        res = self.client.get('/message/pull_user_chain', data={"userId":1}, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_reply_count(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.senderUserName, self.senderUserId)
        self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)


        data = {"userId": self.appliedUserId, "senderUserId": self.senderUserId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        conversation_id = res.json()["conversation_id"]

        data = {"conversationId": conversation_id, "message":"hello!", "replyId":-1}
        res = self.client.put('/message/send_message', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.messageId = res.json()["message_id"]

        res = self.client.get(f'/message/pull_reply_count?messageId={self.messageId}',  content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_reader_list(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.senderUserName, self.senderUserId)
        self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)


        data = {"userId": self.appliedUserId, "senderUserId": self.senderUserId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        conversation_id = res.json()["conversation_id"]

        data = {"conversationId": conversation_id, "message":"hello!", "replyId":-1}
        res = self.client.put('/message/send_message', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.messageId = res.json()["message_id"]

        res = self.client.get(f'/message/pull_reader_list?messageId={self.messageId}',  content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_mark_read_index(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.senderUserName, self.senderUserId)
        self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)


        data = {"userId": self.appliedUserId, "senderUserId": self.senderUserId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        conversation_id = res.json()["conversation_id"]

        data = {"conversationId": conversation_id, "message":"hello!", "replyId":-1}
        res = self.client.put('/message/send_message', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.messageId = res.json()["message_id"]

        data = {"conversationId": conversation_id, "readIndex": 2}
        res = self.client.post(f'/message/mark_read_index', data=data ,content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)