from django.db import models
from utils import utils_time
from django.db import models
from utils.utils_request import return_field

from utils.utils_require import MAX_CHAR_LENGTH

class Message(models.Model):
    id = models.BigAutoField(primary_key=True)
    sender_id = models.IntegerField()
    message_body = models.TextField()
    create_time = models.FloatField(default=utils_time.get_timestamp)
    reply_count = models.IntegerField(default=0)
    reply_id = models.IntegerField(default=-1)


class UserChatChain(models.Model):
    user_id = models.IntegerField()
    conversation_id = models.IntegerField()
    message_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)


class UserReadUserChainTime(models.Model):
    user_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)


class DeletedMessage(models.Model):
    user_id = models.IntegerField()
    message_id = models.IntegerField()