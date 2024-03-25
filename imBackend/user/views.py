import json
from django.http import HttpRequest, HttpResponse
from django.core.files.base import ContentFile

from user.models import Board, User
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, PHONE_NUMBER_LENGTH, CheckRequire, require, check_illegal_char
from utils.utils_time import get_timestamp
from utils.utils_jwt import generate_jwt_token, check_jwt_token
from utils.utils_const import SALT_PASSWARD

from django.contrib.auth.hashers import make_password
import hmac
import hashlib
import os
from django.conf import settings


@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")


@CheckRequire
def login(req: HttpRequest):
    if req.method != "POST":
        return BAD_METHOD
    
    # Request body example: {"userName": "Ashitemaru", "password": "123456"}
    body = json.loads(req.body.decode("utf-8"))
    
    userName = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    if User.objects.filter(name=userName).exists():
        user = User.objects.get(name=userName)
        check_password = hmac.new(SALT_PASSWARD, password.encode("utf-8"), digestmod=hashlib.sha256).digest()
        if user.password == check_password:
            picture_url = None
            if user.picture:
                picture_url = os.path.join(settings.MEDIA_URL, str(user.picture))
            return request_success({"token": generate_jwt_token(userName),
                                    "phoneNumber": user.phoneNumber,
                                    "email": user.email,
                                    "picture": user.picture.url})
        else:
            return request_failed(2, "password or userName wrong", 401)
    else:
        return request_failed(2, "password or userName wrong", 401)
    

@CheckRequire
def register(req: HttpRequest):
    if req.method != "PUT":
        return BAD_METHOD
    
    #Request body example: {"userName": "Ashitemaru", "password": "123456", "ensurePassword": "123456", "phoneNumber": "13243218765", "email":"12345678@qq.com", "picture":file_encoded_in_base64}
    print(req.body)
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
    if User.objects.filter(name=userName).exists():
        return request_failed(2, f"userName {userName} already exists", 400) 
    
    if check_illegal_char(userName, True, True, []) == False:
        return request_failed(4, "only alphabets and number are allowed in userName", 400)
    if check_illegal_char(password, True, True, []) == False:
        return request_failed(4, "Only alphabets and numbers are allowed in password", 400)
    if check_illegal_char(phoneNumber, False, True, ['-', '+']) == False:
        return request_failed(4, "Only numbers, '-' and '+' are allowed in phoneNumber", 400)
    if check_illegal_char(email, True, True, ['@', '.']) == False:
        return request_failed(4, "Only alphabets, numbers, '@' and '.' are allowed in email", 400)
    
    if len(userName) > MAX_CHAR_LENGTH:
        return request_failed(3, f"userName should be no longer than {MAX_CHAR_LENGTH}", 400)
    if len(password) > MAX_CHAR_LENGTH:
        return request_failed(3, f"password should be no longer than {MAX_CHAR_LENGTH}", 400)
    if len(email) > MAX_CHAR_LENGTH:
        return request_failed(3, f"email should be no longer than {MAX_CHAR_LENGTH}", 400)
    if len(phoneNumber) != PHONE_NUMBER_LENGTH:
        return request_failed(3, f"length of phone number should be {PHONE_NUMBER_LENGTH}", 400) 
    

    
    hashed_password = hmac.new(SALT_PASSWARD, password.encode("utf-8"), digestmod=hashlib.sha256).digest()

    #存储用户信息
    user = User(name=userName, password=hashed_password, phoneNumber=phoneNumber, email=email, created_time=get_timestamp())
    user.picture.save(f"{userName}_picture.png", ContentFile(picture), save=True)
    user.save()
    return request_success()
    
    




def check_for_board_data(body):
    board = require(body, "board", "string", err_msg="Missing or error type of [board]")
    # TODO Start: [Student] add checks for type of boardName and userName
    board_name = require(body, "boardName", "string", err_msg="Missing or error type of [boardName]")
    user_name = require(body, "userName", "string", err_msg="Missing or error type of [userName]")
    # TODO End: [Student] add checks for type of boardName and userName
    
    assert 0 < len(board_name) <= 50, "Bad length of [boardName]"
    
    # TODO Start: [Student] add checks for length of userName and board
    assert 0 < len(user_name) <= 50, "Bad length of [userName]"
    assert len(board) == 2500, "Bad length of [board]"
    # TODO End: [Student] add checks for length of userName and board
    
    
    # TODO Start: [Student] add more checks (you should read API docs carefully)
    for i in board:
        assert i in "01", "Bad value of [board]"
    # TODO End: [Student] add more checks (you should read API docs carefully)
    
    return board, board_name, user_name


@CheckRequire
def boards(req: HttpRequest):
    if req.method == "GET":
        params = req.GET
        boards = Board.objects.all().order_by('-created_time')
        return_data = {
            "boards": [
                # Only provide required fields to lower the latency of
                # transmitting LARGE packets through unstable network
                return_field(board.serialize(), ["id", "boardName", "createdAt", "userName"]) 
            for board in boards],
        }
        return request_success(return_data)
        
    
    elif req.method == "POST":
        jwt_token = req.headers.get("Authorization")
        body = json.loads(req.body.decode("utf-8"))
        
        # TODO Start: [Student] Finish the board view function according to the comments below
        
        # First check jwt_token. If not exists, return code 2, "Invalid or expired JWT", http status code 401
        
        # Then invoke `check_for_board_data` to check the body data and get the board_state, board_name and user_name. Check the user_name with the username in jwt_token_payload. If not match, return code 3, "Permission denied", http status code 403
        
        # Find the corresponding user instance by user_name. We can assure that the user exists.
        
        # We lookup if the board with the same name and the same user exists.
        ## If not exists, new an instance of Board type, then save it to the database.
        ## If exists, change corresponding value of current `board`, then save it to the database.

        user_name_jwt = check_jwt_token(jwt_token)
        if user_name_jwt is None:
            return request_failed(2, "Invalid or expired JWT", 401)
        else:
            user_name_jwt = user_name_jwt["username"]
        
        board_state, board_name, user_name = check_for_board_data(body)
        if user_name_jwt != user_name:
            return request_failed(3, "Permission denied", 403)

        user = User.objects.get(name=user_name)
        if Board.objects.filter(user=user, board_name=board_name).exists():
            board = Board.objects.get(user=user, board_name=board_name)
            board.board_state = board_state
            board.created_time = get_timestamp()
            board.save()
            return request_success({"isCreate": False})
        else:
            board = Board(user=user, board_state=board_state, board_name=board_name, created_time=get_timestamp())
            board.save()
            return request_success({"isCreate": True})
        
        return request_failed(1, "Not implemented", 501)
        
        # TODO End: [Student] Finish the board view function according to the comments above
        
    else:
        return BAD_METHOD


@CheckRequire
def boards_index(req: HttpRequest, index: any):
    
    idx = require({"index": index}, "index", "int", err_msg="Bad param [id]", err_code=-1)
    assert idx >= 0, "Bad param [id]"
    
    if req.method == "GET":
        params = req.GET
        board = Board.objects.filter(id=idx).first()  # Return None if not exists
        
        if board:
            return request_success(
                return_field(board.serialize(), ["board", "boardName", "userName"])
            )
            
        else:
            return request_failed(1, "Board not found", status_code=404)
    
    elif req.method == "DELETE":
        # TODO Start: [Student] Finish the board_index view function
        user_name_jwt = check_jwt_token(req.headers.get("Authorization"))
        if user_name_jwt is None:
            return request_failed(2, "Invalid or expired JWT", 401)
        if not Board.objects.filter(id=idx).exists():
            return request_failed(1, "Board not found", 404)
        if Board.objects.get(id=idx).user.name != user_name_jwt["username"]:
            return request_failed(3, "Permission denied", 403)
        Board.objects.get(id=idx).delete()
        return request_success()
        return request_failed(1, "Not implemented", 501)
        # TODO End: [Student] Finish the board_index view function
    
    else:
        return BAD_METHOD


# TODO Start: [Student] Finish view function for user_board
@CheckRequire
def user_board(req: HttpRequest, user_name: str):
    if req.method != "GET":
        return BAD_METHOD
    if not 0 < len(user_name) <= 50:
        return request_failed(-1, "Bad param [userName]", 400)
    if not User.objects.filter(name=user_name).exists():
        return request_failed(1, "User not found", 404)
    user = User.objects.get(name=user_name)
    boards = Board.objects.filter(user=user).order_by('-created_time')

    return request_success({
        "userName": user_name,
        "boards": [return_field(board.serialize(), ["id", "boardName", "createdAt", "userName"]) for board in boards]
    })
# TODO End: [Student] Finish view function for user_board
