from django.urls import path, include
import message.views as views

urlpatterns = [
    path('pull_user_chain', views.pull_user_chain),
    path('send_message', views.send_message),
    path('pull_reply_count', views.pull_reply_count),
    path('pull_reader_list', views.pull_reader_list),
    path('mark_read_index', views.mark_read_index),
    path('delete_message', views.delete_message)
]