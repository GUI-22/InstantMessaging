from django.shortcuts import render
import json
from django.http import HttpRequest, HttpResponse
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import QueryDict


from user.models import User
from friend.models import Friends, UserFriendChain, UserReadFriendChainTime, UserGroup
from message.models import Message, UserChatChain, UserReadUserChainTime
from conversation.models import Conversation, ConversationMember, ConversationChain
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, PHONE_NUMBER_LENGTH, CheckRequire, require, check_illegal_char
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
def apply_friend(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"applyUserName": "Ashitemaru"}
    # 以下为处理json格式的body
    body = json.loads(req.body.decode("utf-8"))
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id_a = jwt_data['userId']
    user_name = jwt_data['userName']
    applyUserName = require(body, "applyUserName", "string", err_msg="Missing or error type of [applyUserName]")
    if User.objects.filter(name=applyUserName, cancled=False).exists():
        user_id_b = User.objects.get(name=applyUserName, cancled=False).id
        if user_id_a == user_id_b:
            return request_failed(2, f"You cannot add yourself to friend list", 400)
        if Friends.objects.filter(user_id_a=user_id_a, user_id_b=user_id_b).exists():
            return request_failed(2, f"You've already added {applyUserName} to your friend list", 400)
        if UserFriendChain.objects.filter(receiver_user_id=user_id_b, sender_user_id=user_id_a, handled=False).exists():
            for user_friend_chain in UserFriendChain.objects.filter(receiver_user_id=user_id_b, sender_user_id=user_id_a, handled=False):
                user_friend_chain.update_time = get_timestamp()
                user_friend_chain.save()
        else:
            user_friend_chain = UserFriendChain(receiver_user_id=user_id_b, sender_user_id=user_id_a, update_time=get_timestamp(), handled=False)
            user_friend_chain.save()

        # user_friend_chain = UserFriendChain(receiver_user_id=user_id_b, sender_user_id=user_id_a, sender_name=user_name, update_time=get_timestamp(), handled=False)
        # user_friend_chain.save()


        channel_layer = get_channel_layer()
        if user_id_b in connected_channels:
            with transaction.atomic():
                # 以下是通过webSocket推送消息；且推送成功才修改“user_read_friend_chain_time"
                return_data = {
                    "sender_id":user_id_a,
                    "sender_name":user_name
                }
                async_to_sync(channel_layer.group_send)(str(user_id_b), {'type': 'receive_friend_application', 'data': return_data})
                # UserReadFriendChainTime.objects.filter(user_id=user_id_b).update(update_time=get_timestamp())
        return request_success()
    else:
        return request_failed(2, "user doesn't exist", 401)
    

@CheckRequire
def handle_friend_apply(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']   
    my_name = User.objects.get(id=my_user_id).name 

    body = json.loads(req.body.decode("utf-8"))
    sender_user_id = require(body, "senderUserId", "int", err_msg="Missing or error type of [senderUserId]")
    agree = require(body, "agree", "string", err_msg="Missing or error type of [agree]")
    
    sender_name = User.objects.get(id=sender_user_id).name
    if agree == "True":
        if UserFriendChain.objects.filter(receiver_user_id=my_user_id, sender_user_id=sender_user_id, handled=False).exists():
            # user_friend_chain = UserFriendChain.objects.get(receiver_user_id=my_user_id, sender_user_id=sender_user_id, handled=False)

            user_friend_chain = UserFriendChain.objects.filter(
                receiver_user_id=my_user_id,
                sender_user_id=sender_user_id,
                handled=False
            ).order_by('update_time').first()

            user_friend_chain.handled = True
            user_friend_chain.save()
            if Friends.objects.filter(user_id_a=my_user_id, user_id_b=sender_user_id).exists():
                return request_failed(2, f"You've already added {sender_name} to your friend list", 400)

            if not UserGroup.objects.filter(user_id=my_user_id, group_name="MyFriends").exists():
                user_group = UserGroup(user_id=my_user_id, group_name="MyFriends")
                user_group.save()

            conversation = Conversation(name=sender_name, create_time=get_timestamp(),update_time=get_timestamp(), private=True)
            conversation.save()
            conversation_id = conversation.id

            friends_a_b = Friends(user_id_a=my_user_id, user_id_b=sender_user_id, conversation_id=conversation_id, update_time=get_timestamp())
            friends_b_a = Friends(user_id_a=sender_user_id, user_id_b=my_user_id, conversation_id=conversation_id, update_time=get_timestamp())
            friends_a_b.save()
            friends_b_a.save()

            conversation_member_me = ConversationMember(conversation_id=conversation_id, member_user_id=my_user_id, join_time=get_timestamp(), update_time=get_timestamp())
            conversation_member_sender = ConversationMember(conversation_id=conversation_id, member_user_id=sender_user_id, join_time=get_timestamp(), update_time=get_timestamp())
            conversation_member_me.save()
            conversation_member_sender.save()

            message = Message(sender_id=my_user_id, message_body="I have accepted your friend request. Now let's start chatting.")
            message.save()

            conversation_message = ConversationChain(conversation_id=conversation_id, message_id=message.id)
            conversation_message.save()

            user_chat_chain_a = UserChatChain(user_id=my_user_id, conversation_id=conversation_id, message_id=message.id, update_time=get_timestamp())
            user_chat_chain_b = UserChatChain(user_id=sender_user_id, conversation_id=conversation_id, message_id=message.id, update_time=get_timestamp())
            user_chat_chain_a.save()
            user_chat_chain_b.save()


            channel_layer = get_channel_layer()
            if sender_user_id in connected_channels:
                with transaction.atomic():
                    return_data = {
                        "friend_id":my_user_id,
                        "friend_name":my_name,
                        "conversation_id":conversation_id
                    }
                    async_to_sync(channel_layer.group_send)(str(sender_user_id), {'type': 'friend_application_agreed', 'data': return_data})




            for member_id in [my_user_id, sender_user_id]:
                user_chat_chain = UserChatChain(user_id=member_id, conversation_id=conversation_id, message_id=message.id, update_time=get_timestamp())
                user_chat_chain.save()

                # 确认 WebSocket 连接建立后再执行推送消息
                if member_id in connected_channels:
                    with transaction.atomic():
                        # 以下是通过webSocket推送消息；且推送成功才修改“user_read_user_chain_time"
                        return_data = {
                            "message":message.message_body,
                            "sender_name":my_name,
                            "sender_id":my_user_id,
                            "conversation_name":Conversation.objects.get(id=conversation_id).name,
                            "conversation_id":conversation_id
                        }
                        async_to_sync(channel_layer.group_send)(str(member_id), {'type': 'receive_message', 'data': return_data})
                        print(f"member_id: {member_id}, here")

                        UserReadUserChainTime.objects.filter(user_id=member_id).update(update_time=get_timestamp())


            return request_success({"conversation_id":conversation.id})

        else:
            return request_failed(7, "Application information invalid", 404)


    elif agree == "False":
        if UserFriendChain.objects.filter(receiver_user_id=my_user_id, sender_user_id=sender_user_id, handled=False).exists():

            # user_friend_chain = UserFriendChain.objects.get(receiver_user_id=my_user_id, sender_user_id=sender_user_id, handled=False)
            
            user_friend_chain = UserFriendChain.objects.filter(
                receiver_user_id=my_user_id,
                sender_user_id=sender_user_id,
                handled=False
            ).order_by('update_time').first()
            
            user_friend_chain.handled = True
            user_friend_chain.save()

            if Friends.objects.filter(user_id_a=my_user_id, user_id_b=sender_user_id).exists():
                return request_failed(2, f"You've already added {sender_name} to your friend list", 400)
            return request_success()
        else:
            return request_failed(7, "Application information invalid", 404)
    else:
        return request_failed(3, "Invalid value for parameter [agree], expect \"True\" or \"False\".", 400)


@CheckRequire
def pull_friend_chain(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']

    # for item in UserFriendChain.objects.filter(receiver_user_id=my_user_id):
    #     print("user_id", item.sender_user_id)

    user_read_friend_chain_time = UserReadFriendChainTime.objects.get(user_id=my_user_id)
    last_read_time = user_read_friend_chain_time.update_time
    user_read_friend_chain_time.update_time = get_timestamp()
    user_read_friend_chain_time.save()


    friend_chain = []
    # for item in UserFriendChain.objects.filter(receiver_user_id=my_user_id, update_time__gt=last_read_time, handled=False):
    for item in UserFriendChain.objects.filter(receiver_user_id=my_user_id, handled=False):
        friend_chain.append({
            "sender_user_id": item.sender_user_id,
            "sender_name": User.objects.get(id=item.sender_user_id).name,
            "sender_picture": get_base64_image(User.objects.get(id=item.sender_user_id))
        })
        
    return request_success({'friend_chain': friend_chain})


@CheckRequire
def pull_friend_list(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']

    friend_list = {}
    for item in Friends.objects.filter(user_id_b=my_user_id):
        group_name = item.group_name
        if group_name not in friend_list:
            friend_list[group_name] = []
        friend = User.objects.get(id=item.user_id_a)
        friend_name = friend.name
        friend_id = friend.id
        conversation_id = item.conversation_id
        friend_list[group_name].append({
            "friend_name": friend_name,
            "friend_id": friend_id,
            "friend_picture": get_base64_image(friend),
            "conversation_id": conversation_id,
            "group_name": group_name,
        })

    for item in UserGroup.objects.filter(user_id=my_user_id):
        group_name = item.group_name
        if group_name not in friend_list:
            friend_list[group_name] = []
    friend_list_return = []
    for group_name, friends in friend_list.items():
        group_data = {
            "group_name": group_name,
            "friend_list": friends
        }
        friend_list_return.append(group_data)

    return request_success({"total_friend_list": friend_list_return})


@CheckRequire
def grouping_friend(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']

    #Request body example: {"friendIds": [1, 2, 3], "groupName":"Classmates"}
    body = json.loads(req.body.decode("utf-8"))
    friend_ids = require(body, "friendIds", "list", err_msg="Missing or error type of [friendIds]")
    group_name = require(body, "groupName", "string", err_msg="Missing or error type of [groupName]")

    friend_id_list = Friends.objects.filter(user_id_b=user_id).values_list('user_id_a', flat=True)
    for friend_id in friend_ids:
        if friend_id not in friend_id_list:
            return request_failed(2, "Invalid user id in friendIds", 401)

    for friend_id in friend_ids:
        friend = Friends.objects.get(user_id_a=friend_id, user_id_b=user_id)
        friend.group_name = group_name
        friend.save()

    if not UserGroup.objects.filter(user_id=user_id, group_name=group_name).exists():
        user_group = UserGroup(user_id=user_id, group_name=group_name)
        user_group.save()

    return request_success()


@CheckRequire
def delete_friend(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']    

    body = json.loads(req.body.decode("utf-8"))

    friend_user_id = require(body, "friendUserId", "int", err_msg="Missing or error type of [friendUserId]")
    
    if not Friends.objects.filter(user_id_a=my_user_id, user_id_b=friend_user_id).exists():
        return request_failed(2, f"Invalid friend user id", 400)
    friends_a_b = Friends.objects.get(user_id_a=my_user_id, user_id_b=friend_user_id)
    friends_a_b.delete()
    friends_b_a = Friends.objects.get(user_id_a=friend_user_id, user_id_b=my_user_id)
    friends_b_a.delete()
    conversation_id = friends_b_a.conversation_id

    conversation = Conversation.objects.get(id=conversation_id)
    conversation.delete()

    conversation_member_me = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=my_user_id)
    conversation_member_friend = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=friend_user_id)
    conversation_member_me.delete()
    conversation_member_friend.delete()

    conversation_messages = ConversationChain.objects.filter(conversation_id=conversation_id)
    for conversation_message in conversation_messages:
        conversation_message.delete()

    user_chat_chain_a = UserChatChain.objects.filter(user_id=my_user_id, conversation_id=conversation_id)
    for chat in user_chat_chain_a:
        chat.delete()
    user_chat_chain_b = UserChatChain.objects.filter(user_id=friend_user_id, conversation_id=conversation_id)
    for chat in user_chat_chain_b:
        chat.delete()
    return request_success()

@CheckRequire
def delete_group(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']    

    body = json.loads(req.body.decode("utf-8"))
    group_name = require(body, "groupName", "string", err_msg="Missing or error type of [groupName]")

    if not UserGroup.objects.filter(user_id=my_user_id, group_name=group_name).exists():
        return request_failed(2, "Invalid groupName", 400)

    friend_id_list = Friends.objects.filter(user_id_b=my_user_id,group_name=group_name).values_list('user_id_a', flat=True)
    friend_id_list = list(friend_id_list)
    if len(friend_id_list) > 0:
        return request_failed(4, f"There're friends in {group_name}", 400)
    
    user_group = UserGroup.objects.filter(user_id=my_user_id, group_name=group_name)
    user_group.delete()
    
    return request_success()

