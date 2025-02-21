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
class ConversationTests(TestCase):
    userName = "Ashitemaru"
    userId = 0
    appliedUserName = "Bob"
    appliedUserId = 0
    appliedUserName_2 = "Alice"
    appliedUserId_2 = 0
    appliedUserName_3 = "Carlo"
    appliedUserId_3 = 0
    conversation_id_1 = 0
    conversation_id_2 = 0
    group_conversation_id = 0
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

        User.objects.filter(name=self.appliedUserName_2).delete()
        user = User.objects.create(name=self.appliedUserName_2, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.name}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()

        self.appliedUserId_2 = user.id

        User.objects.filter(name=self.appliedUserName_3).delete()
        user = User.objects.create(name=self.appliedUserName_3, password=make_password("123456", PASSWORD_SALT), email="email@mail.mail", phoneNumber="88888888", created_time=get_timestamp())
        picture = "picture!"
        user.picture.save(f"{user.name}_picture.png", ContentFile(picture), save=True)
        user.save()

        user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_friend_chain_time.save()

        user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
        user_read_user_chain_time.save()

        self.appliedUserId_3 = user.id


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

        data = {"applyUserName": self.appliedUserName_2}
        header = self.generate_header(self.userName, self.userId)
        res = self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)

        data = {"applyUserName": self.appliedUserName_3}
        header = self.generate_header(self.appliedUserName_2, self.appliedUserId_2)
        res = self.client.post('/friend/apply_friend', data=data, content_type='application/json', **header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_handle_friend_apply(self):
        self.test_apply_friend()
        data = {"userId": self.appliedUserId, "senderUserId": self.userId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.conversation_id_1 = res.json()["conversation_id"]

        data = {"userId": self.appliedUserId_2, "senderUserId": self.userId, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName_2, self.appliedUserId_2))
        self.conversation_id_2 = res.json()["conversation_id"]

        data = {"userId": self.appliedUserId_3, "senderUserId": self.appliedUserId_2, "agree":"True"}
        res = self.client.post('/friend/handle_friend_apply', data=data, content_type='application/json', **self.generate_header(self.appliedUserName_3, self.appliedUserId_3))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)


    def test_create_conversation(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        data = {
            "friendIds":[self.appliedUserId_2, self.appliedUserId],
            "conversationName":"groupChat"
        }
        res = self.client.put('/conversation/create_conversation', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))
        self.group_conversation_id = res.json()["conversation_id"]
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

        
    def test_pull_conversation_list(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        res = self.client.get('/conversation/pull_conversation_list', **self.generate_header(self.appliedUserName, self.appliedUserId))
        # with open("/root/SE/IM/IM-backend/test_output_pull_conv.txt", "w") as file:
        #     json.dump(res.json(), file)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)


    def test_pull_conversation_chain(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        res = self.client.get(f'/conversation/pull_conversation_chain?conversationId={self.conversation_id_1}', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_conversation_member_list(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        res = self.client.get(f'/conversation/pull_conversation_member_list?conversationId={self.conversation_id_1}', **self.generate_header(self.appliedUserName, self.appliedUserId))
        # with open("/root/SE/IM/IM-backend/test_output_pcml.txt", "w") as file:
        #     json.dump(res.json(), file)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_conversation_chain_history(self):
        self.test_apply_friend()
        self.test_handle_friend_apply()
        res = self.client.get(f'/conversation/pull_conversation_chain?conversationId={self.conversation_id_1}&&earliestTime=0.0&&memberId={self.userId}', **self.generate_header(self.appliedUserName, self.appliedUserId))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_appoint_admin(self):
        self.test_create_conversation()
        data = {"conversationId": self.group_conversation_id, "adminIds": [self.appliedUserId]}
        res = self.client.post('/conversation/appoint_admin', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_transfer_ownership(self):
        self.test_create_conversation()
        data = {"conversationId": self.group_conversation_id, "memberId": self.appliedUserId}
        res = self.client.post('/conversation/transfer_ownership', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_quit_conversation(self):
        self.test_appoint_admin()

        data = {"conversationId": self.group_conversation_id}
        res = self.client.delete('/conversation/quit_conversation', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))
        res = self.client.delete('/conversation/quit_conversation', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))
        res = self.client.delete('/conversation/quit_conversation', data=data, content_type='application/json', **self.generate_header(self.appliedUserName_2, self.appliedUserId_2))
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_remove_member(self):
        self.test_appoint_admin()

        data = {"conversationId": self.group_conversation_id, "removeMemberIds":[self.appliedUserId_2]}
        res = self.client.delete('/conversation/remove_member', data=data, content_type='application/json', **self.generate_header(self.appliedUserName, self.appliedUserId))

        data = {"conversationId": self.group_conversation_id, "removeMemberIds":[self.appliedUserId]}
        res = self.client.delete('/conversation/remove_member', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_invite_new_member(self):
        self.test_create_conversation()

        data = {"conversationId": self.group_conversation_id, "newMemberIds": [self.appliedUserId_3]}
        res = self.client.post('/conversation/invite_new_member', data=data, content_type='application/json', **self.generate_header(self.appliedUserName_2, self.appliedUserId_2))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_pull_conversation_apply_chain(self):
        self.test_invite_new_member()

        data = {"conversationId": self.group_conversation_id, "newMemberIds": [self.appliedUserId_3]}
        res = self.client.get(f'/conversation/pull_conversation_apply_chain?conversationId={self.group_conversation_id}', content_type='application/json', **self.generate_header(self.userName, self.userId))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)

    def test_handle_conversation_apply(self):
        self.test_invite_new_member()

        data = {"conversationId": self.group_conversation_id, "invitedUserIds": [self.appliedUserId_3], "agree":"True"}
        res = self.client.post('/conversation/handle_conversation_apply', data=data, content_type='application/json', **self.generate_header(self.userName, self.userId))

        # with open("/root/SE/IM/IM-backend/test_output/test_output_hca.txt", "w") as file:
        #     json.dump(res.json(), file) 
            
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['code'], 0)