from django.shortcuts import render
import json
from django.http import HttpRequest, HttpResponse
from django.core.files.base import ContentFile
from django.db import transaction

from user.models import User
from friend.models import Friends, UserFriendChain, UserReadFriendChainTime
from message.models import Message, UserChatChain, UserReadUserChainTime, DeletedMessage
from conversation.models import Conversation, ConversationMember, ConversationChain
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, PHONE_NUMBER_LENGTH, CheckRequire, require, check_illegal_char, get_param
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token, BlackList
from utils.utils_const import PASSWORD_SALT
from utils.utils_picture import get_base64_image

from django.contrib.auth.hashers import make_password, check_password
import hmac
import hashlib
import os
from django.conf import settings
from django.db.models import Q

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from imBackend.consumer import connected_channels

  
@CheckRequire
def send_message(req: HttpRequest):
    if req.method != "PUT":
        return BAD_METHOD
    # 格式{"conversation_id":"321", "message":"hello"}
    body = json.loads(req.body.decode("utf-8"))
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']
    user_name = jwt_data['userName']
    #验证方法和格式
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")
    message_text = require(body, "message", "string", err_msg="Missing or error type of [message]")
    reply_id = require(body, "replyId", "int", err_msg="Missing or error type of [replyId]")


    if ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():

        if reply_id != -1 :
            if not ConversationChain.objects.filter(conversation_id=conversation_id, message_id=reply_id).exists():
                return request_failed(2, "Invalid reply_id", 400)
            message = Message.objects.get(id=reply_id)
            message.reply_count += 1
            message.save()

        message = Message(sender_id=user_id, message_body=message_text, create_time=get_timestamp(), reply_id=reply_id)
        message.save()

        conversation_chain = ConversationChain(conversation_id=conversation_id, message_id=message.id)
        conversation_chain.save()          

        channel_layer = get_channel_layer()
        
        for conversation_member in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True):
            member_id = conversation_member.member_user_id
            user_chat_chain = UserChatChain(user_id=member_id, conversation_id=conversation_id, message_id=message.id, update_time=get_timestamp())
            user_chat_chain.save()

            # 确认 WebSocket 连接建立后再执行推送消息
            if member_id in connected_channels:
                with transaction.atomic():
                    # 以下是通过webSocket推送消息；且推送成功才修改“user_read_user_chain_time"
                    return_data = {
                        "message":message_text,
                        "message_id":message.id,
                        "sender_name":user_name,
                        "sender_id":user_id,
                        "conversation_name":Conversation.objects.get(id=conversation_id).name,
                        "conversation_id":conversation_id,
                        "reply_id":reply_id
                    }
                    async_to_sync(channel_layer.group_send)(str(member_id), {'type': 'receive_message', 'data': return_data})

                    # UserReadUserChainTime.objects.filter(user_id=member_id).update(update_time=get_timestamp())

        return request_success({"message_id": message.id, "reply_id":reply_id})

    else:
        return request_failed(2, "You're not in this conversation.", 400)

@CheckRequire
def pull_user_chain(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']

    user_read_user_chain_time = UserReadUserChainTime.objects.get(user_id=user_id)
    last_read_time = user_read_user_chain_time.update_time
    user_read_user_chain_time.update_time = get_timestamp()
    user_read_user_chain_time.save()
    user_chain = UserChatChain.objects.filter(user_id=user_id, update_time__gt=last_read_time)
    # user_chain = UserChatChain.objects.filter(user_id=user_id)

    user_chain_return_data = []
    for item in user_chain:
        message = Message.objects.get(id=item.message_id)
        message_body = message.message_body
        sender_id = message.sender_id
        sender = User.objects.get(id=sender_id)
        conversation_id = item.conversation_id
        conversation_name = Conversation.objects.get(id=conversation_id).name
        user_chain_return_data.append({
            "message":message_body,
            "message_id":message.id,
            "sender_name":sender.name,
            "sender_id":sender_id,
            "conversation_name":conversation_name,
            "conversation_id":conversation_id,
            "sender_picture":get_base64_image(sender),
            "send_time":message.create_time,
            "reply_id":message.reply_id,
            "reply_count":message.reply_count
        })

    return request_success({'user_chat_chain': user_chain_return_data})


@CheckRequire
def pull_reply_count(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']

    message_id = req.GET["messageId"]
    if not Message.objects.filter(id=message_id).exists():
        return request_failed(2, "Invalid message_id", 400)
    conversation_id = ConversationChain.objects.get(message_id=message_id).conversation_id
    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():
        return request_failed(2, "Invalid message_id", 400)

    reply_count = Message.objects.get(id=message_id).reply_count

    return request_success({'reply_count': reply_count})


@CheckRequire
def pull_reader_list(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']

    message_id = get_param(req, "messageId", "int", err_msg="Missing or error type of [messageId]", allow_None=False)

    if not Message.objects.filter(id=message_id).exists():
        return request_failed(2, "Invalid message_id", 400)    
    conversation_id = ConversationChain.objects.get(message_id=message_id).conversation_id
    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():
        return request_failed(2, "Invalid message_id", 400)
    
    reader_list = []
    for item in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True):
        if item.read_index >= int(message_id):
            user = User.objects.get(id=item.member_user_id)
            reader_list.append({
                "member_name":user.name,
                "member_user_id":item.member_user_id
            })

    return request_success({'reader_list': reader_list})


@CheckRequire
def mark_read_index(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']
    
    #Request body example: {"conversationId": 1, "readIndex": 2}
    body = json.loads(req.body.decode("utf-8"))
    read_index = require(body, "readIndex", "int", err_msg="Missing or error type of [readIndex]")
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=my_user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)
    
    conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=my_user_id, valid=True)
    conversation_member.read_index = read_index
    conversation_member.save()
    
    return request_success()


@CheckRequire
def delete_message(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']
    
    #Request body example: {"messageId": 1}
    body = json.loads(req.body.decode("utf-8"))
    message_id = require(body, "messageId", "int", err_msg="Missing or error type of [messageId]")
    if not ConversationChain.objects.filter(message_id=message_id).exists():
        return request_failed(2, "Invalid message id", 400)
    conversation_id = ConversationChain.objects.get(message_id=message_id).conversation_id

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=my_user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)
    
    deleted_message = DeletedMessage(user_id=my_user_id, message_id=message_id)
    deleted_message.save()
    
    return request_success()
