from utils import utils_time
from django.db import models
from utils.utils_request import return_field
from utils.utils_require import MAX_CHAR_LENGTH


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_LENGTH)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    email = models.CharField(max_length=MAX_CHAR_LENGTH)
    phoneNumber = models.CharField(max_length=MAX_CHAR_LENGTH)  
    picture = models.ImageField(upload_to='user_pictures', null=True, blank=True) 

    created_time = models.FloatField(default=utils_time.get_timestamp)
    login_time = models.FloatField(default=utils_time.get_timestamp)
    logout_time = models.FloatField(default=utils_time.get_timestamp)

    cancled = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["name"])]