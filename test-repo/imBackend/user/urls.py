from django.urls import path, include
import user.views as views

urlpatterns = [
    path('startup', views.startup),
    path('login', views.login),
    path('register', views.register),
    # path('boards', views.boards),
    # path('boards/<index>', views.boards_index),
    # path('user/<user_name>', views.user_board),
    # TODO End: [Student] add routing paths for `boards/<index>` and `user/<userName>`

]
