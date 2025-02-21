from django.db import models
from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from utils.utils_require import MAX_CHAR_LENGTH


class Conversation(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH, default="")
    create_time = models.FloatField(default=utils_time.get_timestamp)
    update_time = models.FloatField(default=utils_time.get_timestamp)
    private = models.BooleanField(default=True)

class ConversationMember(models.Model):
    conversation_id = models.IntegerField()
    member_user_id = models.IntegerField()
    join_time = models.FloatField(default=utils_time.get_timestamp)
    update_time = models.FloatField(default=utils_time.get_timestamp)
    # commonUser groupOwner admin
    role = models.CharField(max_length=MAX_CHAR_LENGTH, default="commonUser")
    read_index = models.IntegerField(default=-1)
    valid = models.BooleanField(default=True)

class ConversationChain(models.Model):
    conversation_id = models.IntegerField()
    message_id = models.IntegerField()

class ConversationApplyChain(models.Model):
    conversation_id = models.IntegerField()
    invitor_user_id = models.IntegerField()
    invitor_user_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    invited_user_id = models.IntegerField()
    invited_user_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    update_time = models.FloatField(default=utils_time.get_timestamp)
    handled = models.BooleanField(default=False)

class UserReadConversationChainTime(models.Model):
    user_id = models.IntegerField()
    conversation_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)

class AnnouncementChain(models.Model):
    id = models.BigAutoField(primary_key=True)
    conversation_id = models.IntegerField()
    announcement_body = models.TextField()
    