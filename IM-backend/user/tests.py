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
class UserTests(TestCase):
    userName = "Ashitemaru"
    userId = 0
    appliedUserName = "Bobaaa"
    appliedUserId = 0
    # Initializer
    def setUp(self):
        User.objects.filter(name=self.userName).delete()
        user = User.objects.create(name=self.userName, password=make_password("123456AAA", PASSWORD_SALT), email="email@mail.mail", phoneNumber="12388888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.id}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()

        self.userId = user.id
        
        User.objects.filter(name=self.appliedUserName).delete()
        user = User.objects.create(name=self.appliedUserName, password=make_password("123456AAA", PASSWORD_SALT), email="email@mail.mail", phoneNumber="12388888888", created_time=get_timestamp())
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

    def test_register_new_user(self):
        userName = "Aa"+datetime.now().strftime("%mx%dx%Hx%Mx%S")
        data = {"userName": userName, "password": "123456AAA", "ensurePassword": "123456AAA", "phoneNumber": "13243218765", "email":"12345678@qq.com", "picture":PICTURE_STR}
        res = self.client.put('/user/register', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(User.objects.filter(name=userName).exists())

    def test_cancel(self):
        temp_userName = "Temp123"
        User.objects.filter(name=temp_userName).delete()
        data = {"userName": temp_userName, "password": "123456AAA", "ensurePassword": "123456AAA", "phoneNumber": "13243218765", "email":"12345678@qq.com", "picture":PICTURE_STR}
        res = self.client.put('/user/register', data=data, content_type='application/json')

        data = {"userName": temp_userName, "password": "123456AAA"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        data = {"password": "123456AAA"}
        res = self.client.delete('/user/cancel', data=data, content_type='application/json', **{'HTTP_AUTHORIZATION': res.json()['token']})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_login_existing_user_correct_password(self):
        data = {"userName": self.userName, "password": "123456AAA"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        self.jwt_token = res.json()['token']
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)
        self.assertTrue(res.json()['token'].count('.') == 2)

    def test_login_existing_user_wrong_password(self):
        data = {"userName": self.userName, "password": "wrongpassword"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['code'], 2)

    def test_logout_when_already_login(self):
        data = {"userName": self.userName, "password": "123456AAA"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        data = {"userName": self.userName}
        res = self.client.post('/user/logout', data=data, content_type='application/json', **{'HTTP_AUTHORIZATION': res.json()['token']})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_modify_user_info(self):
        data = {"userName": self.userName, "password": "123456AAA"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        token = res.json()['token']
        data = {"newUserName": self.userName, "newPassword": "123456AAA", "oldPassword":"123456AAA", "newPhoneNumber": "13243218765", "newEmail":"12345678@qq.com", "newPicture":""}
        res = self.client.post('/user/modify_user_info', data=data, content_type='application/json', **{'HTTP_AUTHORIZATION': token})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_user_info(self):
        data = {"userName": self.userName, "password": "123456AAA"}
        res = self.client.post('/user/login', data=data, content_type='application/json')
        token = res.json()['token']
        res = self.client.get('/user/pull_user_info?userName=Bob', data=data, content_type='application/json', **{'HTTP_AUTHORIZATION': token})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    