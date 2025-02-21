from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH, unique=True)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    email = models.CharField(max_length=MAX_CHAR_LENGTH)
    phoneNumber = models.CharField(max_length=MAX_CHAR_LENGTH)  
    picture = models.ImageField(upload_to='user_pictures', null=True, blank=True) 

    created_time = models.FloatField(default=utils_time.get_timestamp)
    login_time = models.FloatField(default=utils_time.get_timestamp)


    
    class Meta:
        indexes = [models.Index(fields=["name"])]
        
    def serialize(self):
        boards = Board.objects.filter(user=self)
        return {
            "id": self.id, 
            "name": self.name, 
            "createdAt": self.created_time,
            "boards": [ return_field(board.serialize(), ["id", "boardName", "userName", "createdAt"])
                       for board in boards ]
        }
    
    def __str__(self) -> str:
        return self.name


class Friends(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id_a = models.IntegerField()
    user_id_b = models.IntegerField()
    group_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)
    agree = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user_A', 'user_B']


# 会话管理
# 首先是保存保存会话基本信息的会话表：
# - 全局唯一的会话标志符 conversation_id，整型数据
# - 会话名称 conversation_name，字符串数据
# - 创建时间 create_time，时间戳
# - 更新时间 update_time，时间戳

class Conversation(models.Model):
    conversation_id = models.BigAutoField(primary_key=True)
    conversation_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    create_time = models.FloatField(default=utils_time.get_timestamp)
    update_time = models.FloatField(default=utils_time.get_timestamp)


# 之后是保存会话的成员的会话成员列表，及每个成员在会话中的配置信息：
# - 全局唯一的会话标志符 conversation_id，整型数据
# - 成员的用户标志符 member_user_id，整型数据
# - 成员的加入时间 join_time，时间戳
# - 更新时间 update_time，时间戳
# - 成员当前已读到的消息 index read_index，整型数据
# - 成员在该群中的身份 role_id，整型数据

class ConversationMember(models.Model):
    conversation_id = models.IntegerField()
    member_user_id = models.IntegerField()
    join_time = models.FloatField(default=utils_time.get_timestamp)
    update_time = models.FloatField(default=utils_time.get_timestamp)
    role_id = models.IntegerField()

class Message(models.Model):
    msg_id = models.BigAutoField(primary_key=True)
    msg_body = models.TextField()

class ConversationMessage(models.Model):
    conversation_id = models.IntegerField()
    msg_id = models.ForeignKey(Message, on_delete=models.CASCADE)
    create_time = models.FloatField(default=utils_time.get_timestamp)
    sender_id = models.IntegerField()

class UserChain(models.Model):
    user_id = models.IntegerField()
    conversation_id = models.IntegerField()
    msg_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)












class Board(models.Model):
    # TODO Start: [Student] Finish the model of Board
    
    # id, BigAutoField, primary_key=True
    # user, ForeignKey to User, CASCADE deletion
    # board_state, CharField
    # board_name, CharField
    # created_time, FloatField, default=utils_time.get_timestamp
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board_state = models.CharField(max_length=2500)
    board_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    created_time = models.FloatField(default=utils_time.get_timestamp)
    
    # Meta data
    # Create index on board_name
    # Create unique_together on user and board_name
    class Meta:
        indexes = [models.Index(fields=["board_name"])]
        unique_together = ["user", "board_name"]
    
    # TODO End: [Student] Finish the model of Board


    def serialize(self):
        userName = self.user.name
        return {
            "id": self.id,
            "board": self.board_state, 
            "boardName": self.board_name,
            "userName": userName,
            "createdAt": self.created_time
        }

    def __str__(self) -> str:
        return f"{self.user.name}'s board {self.board_name}"
