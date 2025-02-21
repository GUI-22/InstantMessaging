from django.db import models
from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from utils.utils_require import MAX_CHAR_LENGTH


class Friends(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id_a = models.IntegerField()
    user_id_b = models.IntegerField()
    # a in which group b created
    group_name = models.CharField(max_length=MAX_CHAR_LENGTH, default="MyFriends")
    conversation_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)
    class Meta:
        unique_together = ['user_id_a', 'user_id_b']

class UserFriendChain(models.Model):
    receiver_user_id = models.IntegerField()
    sender_user_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)
    handled = models.BooleanField(default=False)


class UserReadFriendChainTime(models.Model):
    user_id = models.IntegerField()
    update_time = models.FloatField(default=utils_time.get_timestamp)

class UserGroup(models.Model):
    user_id = models.IntegerField()
    group_name = models.CharField(max_length=MAX_CHAR_LENGTH, default="MyFriends")