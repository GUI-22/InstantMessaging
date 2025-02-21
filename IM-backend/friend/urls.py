from django.urls import path, include
import friend.views as views

urlpatterns = [
    path('apply_friend', views.apply_friend),
    path('handle_friend_apply', views.handle_friend_apply),
    path('pull_friend_chain', views.pull_friend_chain),
    path('pull_friend_list', views.pull_friend_list),
    path('delete_friend', views.delete_friend),
    path('grouping_friend', views.grouping_friend),
    path('delete_group', views.delete_group),
]