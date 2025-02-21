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

from channels.testing import WebsocketCommunicator
from django.test import TestCase
from imBackend.consumer import connected_channels, IMConsumer
import asyncio

# Create your tests here.
class FriendTests(TestCase):
    userName = "Ashitemaru"
    userId = 0
    appliedUserName = "Bob"
    appliedUserId = 0
    # Initializer
    def setUp(self):
        User.objects.filter(name=self.userName).delete()
        user = User.objects.create(name=self.userName, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.id}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()

        self.userId = user.id
        
        User.objects.filter(name=self.appliedUserName).delete()
        user = User.objects.create(name=self.appliedUserName, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.name}_picture.png", ContentFile(picture), save=True)
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

    # ! Test section
    # * Tests for login view
    def test_apply_friend(self):
        data = {"applyUserName": self.appliedUserName}
        header = self.generate_header(self.userName, self.userId)
        res = self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_handle_friend_apply(self):
        self.test_apply_friend()
        data = {"userId": self.appliedUserId, "senderUserId": self.userId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        # with open("/root/SE/IM/IM-backend/test_output.txt", "w") as file:
        #     json.dump(res.json(), file)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    
    def test_pull_friend_chain(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {}
        res = self.client.get('/friend/pull_friend_chain', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        # with open("/root/SE/IM/IM-backend/test_output.txt", "w") as file:
        #     json.dump(res.json(), file)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_friend_list(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {}
        res = self.client.get('/friend/pull_friend_list', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        # with open("/root/SE/IM/IM-backend/test_output_a.txt", "w") as file:
        #     json.dump(res.json(), file)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_grouping_friend(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {
            "friendIds":[self.userId],
            "groupName":"Classmates"
        }
        res = self.client.post('/friend/grouping_friend', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_delete_friend(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {
            "friendUserId":self.userId,
        }
        res = self.client.delete('/friend/delete_friend', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_delete_group(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {
            "friendIds":[self.userId],
            "groupName":"Classmates"
        }
        res = self.client.post('/friend/grouping_friend', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        data = {
            "friendIds":[self.userId],
            "groupName":"MyFriends"
        }
        res = self.client.post('/friend/grouping_friend', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        data = {
            "groupName":"Classmates"
        }
        res = self.client.delete('/friend/delete_group', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    