from django.shortcuts import render
import json
from django.http import HttpRequest, HttpResponse
from django.core.files.base import ContentFile
from django.db import transaction

from user.models import User
from friend.models import Friends, UserFriendChain, UserReadFriendChainTime
from message.models import Message, UserChatChain, DeletedMessage
from conversation.models import Conversation, ConversationMember, ConversationChain, ConversationApplyChain, UserReadConversationChainTime, AnnouncementChain
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
def create_conversation(req: HttpRequest):
    if req.method != "PUT":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"friendIds": [1, 2, 3], "conversationName":"Quick_Meet"}
    body = json.loads(req.body.decode("utf-8"))
    friend_ids = require(body, "friendIds", "list", err_msg="Missing or error type of [friendIds]")
    conversation_name = require(body, "conversationName", "string", err_msg="Missing or error type of [conversationName]")

    if len(friend_ids) < 2:
        return request_failed(4, "You cannot create a group chat less than 3 people", 400)

    friend_id_list = Friends.objects.filter(user_id_b=user_id).values_list('user_id_a', flat=True)
    for friend_id in friend_ids:
        if friend_id not in friend_id_list:
            return request_failed(6, "You invite someone who's not your friend", 401)
        if User.objects.filter(id=friend_id, cancled=True).exists():
            return request_failed(6, "You invite someone who's canceled", 401)
    

    conversation = Conversation(create_time=get_timestamp(),update_time=get_timestamp(), private=False, name=conversation_name)
    conversation.save()

    conversation_member_self = ConversationMember(conversation_id=conversation.id, member_user_id=user_id, join_time=get_timestamp(), update_time=get_timestamp(), role="groupOwner", valid=True)
    conversation_member_self.save()

    user_read_conversation_chain_time = UserReadConversationChainTime(conversation_id=conversation.id, user_id=user_id, update_time=get_timestamp())
    user_read_conversation_chain_time.save()

    for friend_id in friend_ids:
        conversation_member_friend = ConversationMember(conversation_id=conversation.id, member_user_id=friend_id, join_time=get_timestamp(), update_time=get_timestamp(), valid=True)
        conversation_member_friend.save()

    # webSocket推送给被加入群聊的user
    channel_layer = get_channel_layer()
    for member_id in friend_ids:
        # 确认 WebSocket 连接建立后再执行推送消息
        if member_id in connected_channels:
            with transaction.atomic():
                # 以下是通过webSocket推送消息
                return_data = {
                    "conversation_name":conversation.name,
                    "conversation_id":conversation.id
                }
                async_to_sync(channel_layer.group_send)(str(member_id), {'type': 'invited_to_conversation', 'data': return_data})

    return request_success({"conversation_id": conversation.id})


@CheckRequire
def pull_conversation_list(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']
    
    conversation_list = []
    for item in ConversationMember.objects.filter(member_user_id=my_user_id, valid=True):
        conversation_id = item.conversation_id
        conversation = Conversation.objects.get(id=item.conversation_id)

        conversation_chain = ConversationChain.objects.filter(conversation_id=conversation_id)
        unread_count = 0
        read_index = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=my_user_id, valid=True).read_index
        for sub_item in conversation_chain:
            if (sub_item.message_id > read_index) and not DeletedMessage.objects.filter(user_id=my_user_id, message_id=sub_item.message_id).exists():
                unread_count += 1
        conversation_name = conversation.name
        if conversation.private is True:
            flag = "True"
            for item in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True):
                if item.member_user_id != my_user_id:
                    conversation_name = User.objects.get(id=item.member_user_id).name
        else:
            flag = "False"
        conversation_list.append({
            "conversation_name": conversation_name,
            "conversation_id": conversation_id,
            "unread_count":unread_count,
            "private":flag
        })

    return request_success({'conversation_list': conversation_list})


@CheckRequire
def pull_conversation_chain(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]

    conversation_id = req.GET["conversationId"]
    
    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)

    conversation_chain = ConversationChain.objects.filter(conversation_id=conversation_id)
    conversation_chain_return_data = []
    for item in conversation_chain:
        if DeletedMessage.objects.filter(user_id=user_id, message_id=item.message_id).exists():
            continue

        reader_list = []
        for sub_item in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True):
            if sub_item.read_index >= int(item.message_id):
                user = User.objects.get(id=sub_item.member_user_id)
                reader_list.append({
                    "member_name":user.name,
                    "member_user_id":sub_item.member_user_id
                })

        message = Message.objects.get(id=item.message_id)
        message_body = message.message_body
        sender_id = message.sender_id
        if User.objects.filter(id=sender_id).exists():
            sender = User.objects.get(id=sender_id)
            conversation_chain_return_data.append({
                "message":message_body,
                "message_id":message.id,
                "sender_name":sender.name,
                "sender_id":sender_id,
                "sender_picture":get_base64_image(sender),
                "send_time":message.create_time,
                "reply_id":message.reply_id,            
                "reply_count":message.reply_count,
                "reader_list": reader_list
            })
    
    # unread_count = 0
    # read_index = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=user_id, valid=True).read_index
    # for item in conversation_chain:
    #     if (item.message_id > read_index):
    #         unread_count += 1

    # return request_success({'conversation_chain': conversation_chain_return_data, 'unread_count':unread_count})

    return request_success({'conversation_chain': conversation_chain_return_data})


@CheckRequire
def pull_conversation_chain_history(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]

    conversation_id = get_param(req, "conversationId", "int", err_msg="Missing or error type of [conversationId]", allow_None=False)
    start_time = get_param(req, "startTime", "float", err_msg="Missing or error type of [startTime]", allow_None=True)
    end_time = get_param(req, "endTime", "float", err_msg="Missing or error type of [endTime]", allow_None=True)
    # member_id = get_param(req, "memberId", "int", err_msg="Missing or error type of [memberId]", allow_None=True)
    member_names = get_param(req, "memberNames", "string", err_msg="Missing or error type of [memberNames]", allow_None=True)
    try:
        if member_names:
            member_names = member_names.split("|")
        else:
            member_names = []
    except:
        raise KeyError("Missing or error type of [memberNames]", -2)
    
    if start_time > end_time:
        return request_failed(2, "end time shouldn't be earlier than start time", 400)


    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)

    conversation_chain = ConversationChain.objects.filter(conversation_id=conversation_id)
    conversation_chain_return_data = []
    for item in conversation_chain:
        if DeletedMessage.objects.filter(user_id=user_id, message_id=item.message_id).exists():
            continue
        message = Message.objects.get(id=item.message_id)
        if (start_time is None or float(start_time) <= message.create_time) and (end_time is None or float(end_time) >= message.create_time) and (member_names == [] or User.objects.get(id=message.sender_id).name in member_names):
            message_body = message.message_body
            sender_id = message.sender_id
            sender = User.objects.get(id=sender_id)
            conversation_chain_return_data.append({
                "message":message_body,
                "message_id":message.id,
                "sender_name":sender.name,
                "sender_id":sender_id,
                "sender_picture":get_base64_image(sender),
                "send_time":message.create_time,
                "reply_id":message.reply_id,
                "reply_count":message.reply_count
            })

    return request_success({'conversation_chain': conversation_chain_return_data})


@CheckRequire
def pull_conversation_member_list(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]
    conversation_id = req.GET["conversationId"]
    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)
    member_list = []

    announcement_chain = AnnouncementChain.objects.filter(conversation_id=conversation_id)
    announcement_chain_return_data = []
    for item in announcement_chain:
        announcement_chain_return_data.append({
            "announcement_body":item.announcement_body,
            "announcement_id":item.id
        })
    
    for item in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True):
        member_id = item.member_user_id
        member = User.objects.get(id=member_id)
        member_list.append({
            "member_name": member.name,
            "member_id": member.id,
            "member_picture": get_base64_image(member),
            "role": item.role
        })

    return request_success({'member_list': member_list, 'announcement_chain': announcement_chain_return_data})


@CheckRequire
def appoint_admin(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"conversationId": 123, "adminIds": [1, 2, 3]}
    body = json.loads(req.body.decode("utf-8"))
    admin_ids = require(body, "adminIds", "list", err_msg="Missing or error type of [adminIds]")
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, role="groupOwner", valid=True).exists():
        return request_failed(2, "You are not the group owner of the conversation", 400)

    member_id_list = ConversationMember.objects.filter(conversation_id=conversation_id, valid=True).values_list('member_user_id', flat=True)

    for admin_id in admin_ids:
        if admin_id not in member_id_list:
            return request_failed(6, "You appoint someone who's not in this conversation", 401)
    
    for admin_id in admin_ids:
        conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=admin_id, valid=True)
        conversation_member.role = "admin"
        conversation_member.save()

        user_read_conversation_chain_time = UserReadConversationChainTime(conversation_id=conversation_id, user_id=admin_id, update_time=get_timestamp())
        user_read_conversation_chain_time.save()


    return request_success()


@CheckRequire
def transfer_ownership(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"conversationId": 123, "memberId": 2}
    body = json.loads(req.body.decode("utf-8"))
    member_id = require(body, "memberId", "int", err_msg="Missing or error type of [memberId]")
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, role="groupOwner", valid=True).exists():
        return request_failed(2, "You are not the group owner of the conversation", 400)

    member_id_list = ConversationMember.objects.filter(conversation_id=conversation_id, valid=True).values_list('member_user_id', flat=True)

    if member_id not in member_id_list:
        return request_failed(6, "You appoint someone who's not in this conversation", 401)
    
    conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=member_id, valid=True)
    conversation_member.role = "groupOwner"
    conversation_member.save()

    conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=user_id, valid=True)
    conversation_member.role = "admin"
    conversation_member.save()

    if not UserReadConversationChainTime.objects.filter(conversation_id=conversation_id, user_id=member_id).exists():
        user_read_conversation_chain_time = UserReadConversationChainTime(conversation_id=conversation_id, user_id=member_id, update_time=get_timestamp())
        user_read_conversation_chain_time.save()

    return request_success()


@CheckRequire
def quit_conversation(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"conversationId": 123}
    body = json.loads(req.body.decode("utf-8"))
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():
        return request_failed(2, "You are not in this conversation", 400)
    
    conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=user_id, valid=True)
    if conversation_member.role == "groupOwner":
        return request_failed(2, "Group owner cannot quit conversation", 400)
    conversation_member.valid = False
    conversation_member.save()

    if (conversation_member.role == "admin" or conversation_member.role == "groupOwner"):
        user_read_conversation_chain_time = UserReadConversationChainTime.objects.get(conversation_id=conversation_id, user_id=user_id)
        user_read_conversation_chain_time.delete()

    return request_success()


@CheckRequire
def remove_member(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"conversationId": 123, "removeMemberIds":[1, 2, 3]}
    body = json.loads(req.body.decode("utf-8"))
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")
    remove_member_ids = require(body, "removeMemberIds", "list", err_msg="Missing or error type of [removeMemberIds]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():
        return request_failed(2, "You are not in this conversation", 400)
    
    my_role = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=user_id, valid=True).role
    if my_role == "commonUser":
        return request_failed(2, "You have no right", 400)
        
    elif my_role == "groupOwner":
        member_id_list = ConversationMember.objects.filter(conversation_id=conversation_id, valid=True).values_list('member_user_id', flat=True)
        for remove_member_id in remove_member_ids:
            if remove_member_id not in member_id_list:
                return request_failed(2, "You have no right", 400)
        if user_id in remove_member_ids:
            return request_failed(2, "You have no right", 400)
        
        for remove_member_id in remove_member_ids:
            conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=remove_member_id, valid=True)
            conversation_member.valid = False
            conversation_member.save()

            if (conversation_member.role == "admin"):
                user_read_conversation_chain_time = UserReadConversationChainTime.objects.get(conversation_id=conversation_id, user_id=remove_member_id)
                user_read_conversation_chain_time.delete()

    elif my_role == "admin":
        member_id_list = ConversationMember.objects.filter(conversation_id=conversation_id, role="commonUser", valid=True).values_list('member_user_id', flat=True)
        for remove_member_id in remove_member_ids:
            if remove_member_id not in member_id_list:
                return request_failed(2, "You have no right", 400)
        
        for remove_member_id in remove_member_ids:
            conversation_member = ConversationMember.objects.get(conversation_id=conversation_id, member_user_id=remove_member_id, valid=True)
            conversation_member.valid = False
            conversation_member.save()

    return request_success()


@CheckRequire
def invite_new_member(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data['userId']    

    #Request body example: {"conversationId": 123, "newMemberIds": [1, 2, 3]}
    body = json.loads(req.body.decode("utf-8"))
    new_member_ids = require(body, "newMemberIds", "list", err_msg="Missing or error type of [newMemberIds]")
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")

    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists():
        return request_failed(2, "You are not in this conversation", 400)

    member_id_list = ConversationMember.objects.filter(conversation_id=conversation_id, valid=True).values_list('member_user_id', flat=True)
    for new_member_id in new_member_ids:
        if new_member_id in member_id_list:
            return request_failed(6, "You invite someone who's already in this conversation", 401)    

    friend_id_list = Friends.objects.filter(user_id_b=user_id).values_list('user_id_a', flat=True)
    for new_member_id in new_member_ids:
        if new_member_id not in friend_id_list:
            return request_failed(6, "You invite someone who's not your friend", 401)
        if User.objects.filter(id=new_member_id, cancled=True).exists():
            return request_failed(6, "You invite someone who's canceled", 401)
        

    if not ConversationApplyChain.objects.filter(
            conversation_id= conversation_id, 
            invitor_user_id= user_id, 
            invited_user_id = new_member_id,
            handled = False
        ).exists():
        for new_member_id in new_member_ids:
            conversation_apply_chain = ConversationApplyChain(
                conversation_id= conversation_id, 
                invitor_user_id= user_id, 
                invitor_user_name= User.objects.get(id=user_id).name, 
                invited_user_id = new_member_id,
                invited_user_name = User.objects.get(id=new_member_id).name, 
                update_time = get_timestamp(),
                handled = False
            )
            conversation_apply_chain.save()
        

        checker_ids = []
        checker_ids.append(ConversationMember.objects.get(conversation_id=conversation_id, valid=True, role="groupOwner").member_user_id)
        for conversation_member in ConversationMember.objects.filter(conversation_id=conversation_id, valid=True, role="admin"):
            checker_ids.append(conversation_member.member_user_id)
        
        channel_layer = get_channel_layer()
        for checker_id in checker_ids:
            # 确认 WebSocket 连接建立后再执行推送消息
            if checker_id in connected_channels:
                with transaction.atomic():
                    return_data = {
                        "applier_ids":new_member_ids,
                        "conversation_name":Conversation.objects.get(id=conversation_id).name,
                        "conversation_id":conversation_id
                    }
                    async_to_sync(channel_layer.group_send)(str(checker_id), {'type': 'receive_conversation_application', 'data': return_data})

                    UserReadConversationChainTime.objects.filter(user_id=checker_id).update(update_time=get_timestamp())

    return request_success()

### 
# 这个版本的pull_conversation_apply_chain在url中需要传入conversation_id
# @CheckRequire
# def pull_conversation_apply_chain(req: HttpRequest):
#     if req.method != "GET":
#         return BAD_METHOD
#     jwt_token = req.headers.get("Authorization")
#     jwt_data = check_jwt_token(jwt_token)
#     if jwt_data is None:
#         return request_failed(6, "invalid or expired JWT", 401)
#     my_user_id = jwt_data['userId']

#     conversation_id = get_param(req, "conversationId", "int", allow_None=False)

#     if not UserReadConversationChainTime.objects.filter(user_id=my_user_id, conversation_id=conversation_id).exists():
#         return request_failed(2, "You have no right", 400)

#     user_read_conversation_chain_time = UserReadConversationChainTime.objects.get(user_id=my_user_id, conversation_id=conversation_id)
#     last_read_time = user_read_conversation_chain_time.update_time
#     user_read_conversation_chain_time.update_time = get_timestamp()
#     user_read_conversation_chain_time.save()

#     conversation_apply_chain = []
#     for item in ConversationApplyChain.objects.filter(conversation_id=conversation_id, update_time__gt=last_read_time, handled=False):
#         conversation_apply_chain.append({
#             "invitor_user_id": item.invitor_user_id,
#             "invitor_user_name": item.invitor_user_name,
#             "invited_user_id": item.invited_user_id,
#             "invited_user_name": item.invited_user_name,
#         })
        
#     return request_success({'conversation_apply_chain': conversation_apply_chain})


@CheckRequire
def pull_conversation_apply_chain(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']

    conversation_id = req.GET["conversationId"]

    total_conversation_apply_chain = []

    if not ConversationMember.objects.filter(Q(role="admin") | Q(role="groupOwner"), member_user_id=my_user_id, valid=True, conversation_id=conversation_id).exists():
        return request_failed(6, "You're not the admin or group owner of this conversation", 401)
    else:
        
        # conversation_id = conversation_member.conversation_id
        # user_read_conversation_chain_time = UserReadConversationChainTime.objects.get(user_id=my_user_id, conversation_id=conversation_id)
        # last_read_time = user_read_conversation_chain_time.update_time
        # user_read_conversation_chain_time.update_time = get_timestamp()
        # user_read_conversation_chain_time.save()

        one_conversation_data = {}
        one_conversation_data["conversation_id"] = conversation_id
        one_conversation_data["conversation_name"] = Conversation.objects.get(id=conversation_id).name
        
        conversation_apply_chain = []
        # for item in ConversationApplyChain.objects.filter(conversation_id=conversation_id, update_time__gt=last_read_time, handled=False):
        for item in ConversationApplyChain.objects.filter(conversation_id=conversation_id, handled=False):
            conversation_apply_chain.append({
                "invitor_user_id": item.invitor_user_id,
                "invitor_user_name": item.invitor_user_name,
                "invited_user_id": item.invited_user_id,
                "invited_user_name": item.invited_user_name,
            })
        one_conversation_data["conversation_apply_chain"] = conversation_apply_chain
        # if len(conversation_apply_chain) > 0:
        #     total_conversation_apply_chain.append(one_conversation_data)
        total_conversation_apply_chain.append(one_conversation_data)
        
    return request_success({'total_conversation_apply_chain': total_conversation_apply_chain})


@CheckRequire
def handle_conversation_apply(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    my_user_id = jwt_data['userId']

    #Request body example: {"conversationId": 123, "invitedUserIds": [1, 2, 3], "agree":"True"}
    body = json.loads(req.body.decode("utf-8"))
    invited_user_ids = require(body, "invitedUserIds", "list", err_msg="Missing or error type of [invitedUserIds]")
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")
    agree = require(body, "agree", "string", err_msg="Missing or error type of [agree]")

    if (not ConversationMember.objects.filter(member_user_id=my_user_id, conversation_id=conversation_id, role="groupOwner", valid=True).exists() and 
        not ConversationMember.objects.filter(member_user_id=my_user_id, conversation_id=conversation_id, role="admin", valid=True).exists()):
        return request_failed(2, "You have no right", 400)
    
    if agree == "True":
        for invited_user_id in invited_user_ids:
            if not ConversationApplyChain.objects.filter(conversation_id=conversation_id, invited_user_id=invited_user_id, handled=False).exists():
                return request_failed(7, "Application information invalid", 404)
        
        for invited_user_id in invited_user_ids:
            conversation_apply_chain = ConversationApplyChain.objects.get(conversation_id=conversation_id, invited_user_id=invited_user_id, handled=False)
            conversation_apply_chain.handled = True
            conversation_apply_chain.save()

            if ConversationMember.objects.filter(conversation_id = conversation_id, member_user_id = invited_user_id).exists():
                conversation_member = ConversationMember.objects.get(conversation_id = conversation_id, member_user_id = invited_user_id)
                conversation_member.valid = True
                conversation_member.join_time = get_timestamp()
                conversation_member.update_time = get_timestamp()
                conversation_member.role = "commonUser"
                conversation_member.save()            

            else:
                conversation_member = ConversationMember(
                    conversation_id = conversation_id,
                    member_user_id = invited_user_id,
                    join_time = get_timestamp(),
                    update_time = get_timestamp(),
                    role = "commonUser",
                    read_index = -1,
                    valid = True
                )
                conversation_member.save()

            # webSocket推送给被加入群聊的user
            channel_layer = get_channel_layer()
            if invited_user_id in connected_channels:
                with transaction.atomic():
                    # 以下是通过webSocket推送消息
                    return_data = {
                        "conversation_name":Conversation.objects.get(id=conversation_id).name,
                        "conversation_id":conversation_id
                    }
                    async_to_sync(channel_layer.group_send)(str(invited_user_id), {'type': 'invited_to_conversation', 'data': return_data})

        return request_success()
        
    elif agree == "False":
        for invited_user_id in invited_user_ids:
            if not ConversationApplyChain.objects.filter(conversation_id=conversation_id, invited_user_id=invited_user_id, handled=False).exists():
                return request_failed(7, "Application information invalid", 404)
        
        for invited_user_id in invited_user_ids:
            conversation_apply_chain = ConversationApplyChain.objects.get(conversation_id=conversation_id, invited_user_id=invited_user_id, handled=False)
            conversation_apply_chain.handled = True
            conversation_apply_chain.save()

        return request_success()

    else:
        return request_failed(3, "Invalid value for parameter [agree], expect \"True\" or \"False\".", 400)


@CheckRequire
def put_announcement(req: HttpRequest):
    if req.method != "PUT":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]

    #Request body example: {"conversationId": 123, "announcement":"AAA"}
    body = json.loads(req.body.decode("utf-8"))
    conversation_id = require(body, "conversationId", "int", err_msg="Missing or error type of [conversationId]")
    announcement_body = require(body, "announcementBody", "string", err_msg="Missing or error type of [announcementBody]")
    
    if (not ConversationMember.objects.filter(member_user_id=user_id, conversation_id=conversation_id, role="groupOwner", valid=True).exists() and 
        not ConversationMember.objects.filter(member_user_id=user_id, conversation_id=conversation_id, role="admin", valid=True).exists()):
        return request_failed(2, "You have no right to put announcement", 400)
    
    announcement_chain = AnnouncementChain(conversation_id=conversation_id, announcement_body=announcement_body)
    announcement_chain.save()

    return request_success({"announcement_id":announcement_chain.id})


@CheckRequire
def pull_announcement(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    # 验证JWT
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]

    conversation_id = req.GET["conversationId"]
    
    if not ConversationMember.objects.filter(conversation_id=conversation_id, member_user_id=user_id, valid=True).exists() :
        return request_failed(6, "You're not in this conversation", 401)

    announcement_chain = AnnouncementChain.objects.filter(conversation_id=conversation_id)
    announcement_chain_return_data = []
    for item in announcement_chain:
        announcement_chain_return_data.append({
            "announcement_body":item.announcement_body,
            "announcement_id":item.id
        })
    
    return request_success({'announcement_chain': announcement_chain_return_data})

