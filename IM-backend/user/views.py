import json
from django.http import HttpRequest, HttpResponse
from django.core.files.base import ContentFile

from user.models import User
from friend.models import Friends, UserFriendChain, UserReadFriendChainTime, UserGroup
from message.models import Message, UserChatChain, UserReadUserChainTime, DeletedMessage
from conversation.models import Conversation, ConversationMember, ConversationChain, ConversationApplyChain, UserReadConversationChainTime
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


@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")


@CheckRequire
def login(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    # 以下为处理json格式的body
    body = json.loads(req.body.decode("utf-8"))
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")

    if User.objects.filter(name=userName, cancled=False).exists():
        user = User.objects.get(name=userName, cancled=False)
        if check_password(password, user.password):
            if user.logout_time < user.login_time:
                return request_failed(5, "can't login twice", 400)
            user.login_time = get_timestamp()
            user.save()
            return request_success({"token": generate_jwt_token(userName, user.id),
                                    "phoneNumber": user.phoneNumber,
                                    "userId": user.id,
                                    "email": user.email,
                                    # "picture": user.picture.url})
                                    "picture": get_base64_image(user)})
        else:
            return request_failed(2, "password or userName wrong", 401)
    else:
        return request_failed(2, "password or userName wrong", 401)
    
    
@CheckRequire
def logout(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    # Request body example: {}
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    BlackList.add(jwt_token)
    user = User.objects.get(id=jwt_data["userId"], cancled=False)
    if user.login_time > user.logout_time:
        user.logout_time = get_timestamp()
        user.save()
        return request_success()
    else:
        return request_failed(5, "please login first", 400)
    

@CheckRequire
def register(req: HttpRequest):
    if req.method != "PUT":
        return BAD_METHOD
    
    #Request body example: {"userName": "Ashitemaru", "password": "123456", "ensurePassword": "123456", "phoneNumber": "13243218765", "email":"12345678@qq.com", "picture":file_encoded_in_base64}
    body = json.loads(req.body.decode("utf-8"))

    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    ensurePassword = require(body, "ensurePassword", "string", err_msg="Missing or error type of [ensurePassword]")
    phoneNumber = require(body, "phoneNumber", "string", err_msg="Missing or error type of [phoneNumber]")
    email = require(body, "email", "string", err_msg="Missing or error type of [email]")
    picture = require(body, "picture", "file", err_msg="Missing or error type of [picture]")

    # 错误处理
    if password != ensurePassword:
        return request_failed(2, "password and ensurePassword are different", 400)
    if User.objects.filter(name=userName, cancled=False).exists():
        return request_failed(2, f"userName {userName} already exists", 400) 

    if check_illegal_char(userName, True, True, []) == False:
        return request_failed(4, "only alphabets and number are allowed in userName", 400)
    if check_illegal_char(password, True, True, []) == False:
        return request_failed(4, "Only alphabets and numbers are allowed in password", 400)
    if check_illegal_char(phoneNumber, False, True, ['-', '+']) == False:
        return request_failed(4, "Only numbers, '-' and '+' are allowed in phoneNumber", 400)
    if check_illegal_char(email, True, True, ['@', '.']) == False:
        return request_failed(4, "Only alphabets, numbers, '@' and '.' are allowed in email", 400)
    
    if len(userName) > 16 or len(userName) < 4:
        return request_failed(3, f"length of user name wrong", 400)
    if len(password) > 18 or len(password) < 6:
        return request_failed(3, f"length of password wrong", 400)
    if len(email) > MAX_CHAR_LENGTH:
        return request_failed(3, f"email should be no longer than {MAX_CHAR_LENGTH}", 400)
    if len(phoneNumber) != PHONE_NUMBER_LENGTH:
        return request_failed(3, f"length of phone number should be {PHONE_NUMBER_LENGTH}", 400) 
    
    #存储用户信息
    user = User(name=userName, password=make_password(password, PASSWORD_SALT), phoneNumber=phoneNumber, email=email, created_time=get_timestamp())
    user.save()
    user.picture.save(f"{user.id}_picture.jpg", ContentFile(picture), save=True)
    user.save()

    user_read_friend_chain_time = UserReadFriendChainTime(user_id=user.id, update_time=get_timestamp())
    user_read_friend_chain_time.save()

    user_read_user_chain_time = UserReadUserChainTime(user_id=user.id, update_time=get_timestamp())
    user_read_user_chain_time.save()

    user_group = UserGroup(user_id=user.id)
    user_group.save()

    return request_success()
    

@CheckRequire
def cancel(req: HttpRequest):
    if req.method != "DELETE":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    BlackList.add(jwt_token)
    user_id = jwt_data["userId"]
    # Request body example: {"password": "123456"}

    body = json.loads(req.body.decode("utf-8"))
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    user = User.objects.get(id=user_id)
    if check_password(password, user.password):
        user.cancled = True
        user.name = user.name + "（已注销）"
        user.save()

        for item in ConversationMember.objects.filter(member_user_id=user_id, valid=True):
            if Conversation.objects.filter(id=item.conversation_id, private=False).exists():
                item.valid = False
                item.save()
                if item.role == "groupOwner":  
                    for sub_item in ConversationMember.objects.filter(conversation_id=item.conversation_id, valid=True):
                        sub_item.role = "groupOwner"
                        sub_item.save()
                        break
                

        # user.picture.delete()  # 删除用户的图片文件（如果存在）
        # user.delete()  # 删除用户对象及其关联的数据

        # for item in UserChatChain.objects.filter(user_id=user_id):
        #     item.delete()
        # for item in UserReadUserChainTime.objects.filter(user_id=user_id):
        #     item.delete()

        # for item in UserReadFriendChainTime.objects.filter(user_id=user_id):
        #     item.delete()

        # for item in UserGroup.objects.filter(user_id=user_id):
        #     item.delete()
        # for item in UserFriendChain.objects.filter(receiver_user_id=user_id):
        #     item.delete()
        # for item in UserFriendChain.objects.filter(sender_user_id=user_id):
        #     item.delete()
        # for item in Friends.objects.filter(user_id_a=user_id):
        #     item.delete()
        # for item in Friends.objects.filter(user_id_b=user_id):
        #     item.delete()

        # for item in ConversationMember.objects.filter(member_user_id=user_id):
        #     if Conversation.objects.filter(id=item.conversation_id, private=True).exists():
        #         conversation = Conversation.objects.get(id=item.conversation_id)
        #         conversation.delete()
        #         for sub_item in ConversationMember.objects.filter(conversation_id=conversation.id):
        #             sub_item.delete()

        # for item in ConversationMember.objects.filter(member_user_id=user_id):
        #     item.delete()
        # for item in ConversationApplyChain.objects.filter(invitor_user_id=user_id):
        #     item.delete()
        # for item in ConversationApplyChain.objects.filter(invited_user_id=user_id):
        #     item.delete()
        # for item in UserReadConversationChainTime.objects.filter(user_id=user_id):
        #     item.delete()

        # for item in DeletedMessage.objects.filter(user_id=user_id):
        #     item.delete()

        return request_success()
    else:
        return request_failed(2, "password wrong", 401)


@CheckRequire
def pull_user_info(req: HttpRequest):
    if req.method != "GET":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_name = req.GET["userName"]

    # user_name = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    user_list = []
    for user in User.objects.filter(name=user_name, cancled=False):
        user_list.append({
            "user_name": user.name,
            "user_id": user.id,
            "user_phone_number": user.phoneNumber,
            "user_email": user.email,
            "user_picture": get_base64_image(user)
        })
    return request_success({'user_list': user_list})


@CheckRequire
def modify_user_info(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    jwt_token = req.headers.get("Authorization")
    jwt_data = check_jwt_token(jwt_token)
    if jwt_data is None:
        return request_failed(6, "invalid or expired JWT", 401)
    user_id = jwt_data["userId"]
    user = User.objects.get(id=user_id)

    body = json.loads(req.body.decode("utf-8"))

    # old_password = require(body, "oldPassword", "string", err_msg="Missing or error type of [oldPassword]")
    # if not check_password(old_password, user.password):
    #     return request_failed(6, "Password Wrong", 401)

    if body["newUserName"] != "":
        new_user_name = require(body, "newUserName", "string", err_msg="Missing or error type of [newUserName]")
        if new_user_name != user.name and User.objects.filter(name=new_user_name, cancled=False).exists():
            return request_failed(2, f"userName {new_user_name} already exists", 400) 
        if check_illegal_char(new_user_name, True, True, []) == False:
            return request_failed(4, "only alphabets and number are allowed in userName", 400)
        if len(new_user_name) > MAX_CHAR_LENGTH:
            return request_failed(3, f"userName should be no longer than {MAX_CHAR_LENGTH}", 400)

    if body["newPassword"] != "":
        old_password = require(body, "oldPassword", "string", err_msg="Missing or error type of [oldPassword]")
        new_password = require(body, "newPassword", "string", err_msg="Missing or error type of [newPassword]")
        if check_illegal_char(new_password, True, True, []) == False:
            return request_failed(4, "Only alphabets and numbers are allowed in password", 400)
        if len(new_password) > MAX_CHAR_LENGTH:
            return request_failed(3, f"password should be no longer than {MAX_CHAR_LENGTH}", 400)
        if not check_password(old_password, user.password):
            return request_failed(6, "Password Wrong", 401)

    if body["newPhoneNumber"] != "":
        old_password = require(body, "oldPassword", "string", err_msg="Missing or error type of [oldPassword]")
        new_phone_number = require(body, "newPhoneNumber", "string", err_msg="Missing or error type of [newPhoneNumber]")
        if check_illegal_char(new_phone_number, False, True, ['-', '+']) == False:
            return request_failed(4, "Only numbers, '-' and '+' are allowed in phoneNumber", 400)
        if len(new_phone_number) != PHONE_NUMBER_LENGTH:
            return request_failed(3, f"length of phone number should be {PHONE_NUMBER_LENGTH}", 400) 
        if not check_password(old_password, user.password):
            return request_failed(6, "Password Wrong", 401)

    if body["newEmail"] != "":
        old_password = require(body, "oldPassword", "string", err_msg="Missing or error type of [oldPassword]")
        new_email = require(body, "newEmail", "string", err_msg="Missing or error type of [newEmail]")
        if check_illegal_char(new_email, True, True, ['@', '.']) == False:
            return request_failed(4, "Only alphabets, numbers, '@' and '.' are allowed in email", 400)
        if len(new_email) > MAX_CHAR_LENGTH:
            return request_failed(3, f"email should be no longer than {MAX_CHAR_LENGTH}", 400)
        if not check_password(old_password, user.password):
            return request_failed(6, "Password Wrong", 401)


    if body["newUserName"] != "":
        new_user_name = require(body, "newUserName", "string", err_msg="Missing or error type of [newUserName]")
        user.name = new_user_name

    if body["newPassword"] != "":
        new_password = require(body, "newPassword", "string", err_msg="Missing or error type of [newPassword]")
        user.password = make_password(new_password, PASSWORD_SALT)

    if body["newPhoneNumber"] != "":
        new_phone_number = require(body, "newPhoneNumber", "string", err_msg="Missing or error type of [newPhoneNumber]")
        user.phoneNumber = new_phone_number

    if body["newEmail"] != "":
        new_email = require(body, "newEmail", "string", err_msg="Missing or error type of [newEmail]")
        user.email = new_email

    user.save()
    if body["newPicture"] != "":
        new_picture = require(body, "newPicture", "file", err_msg="Missing or error type of [newPicture]")
        user.picture.delete()
        user.picture.save(f"{user.id}_picture.jpg", ContentFile(new_picture), save=True)

    user.save()
    return request_success({"token": generate_jwt_token(user.name, user.id),
                                    "phoneNumber": user.phoneNumber,
                                    "userId": user.id,
                                    "email": user.email,
                                    # "picture": user.picture.url})
                                    "picture": get_base64_image(user)})

