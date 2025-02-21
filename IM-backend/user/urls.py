from django.urls import path, include
import user.views as views

urlpatterns = [
    path('login', views.login),
    path('register', views.register),
    path('logout', views.logout),
    path('cancel', views.cancel),
    path('modify_user_info', views.modify_user_info),
    path('pull_user_info', views.pull_user_info)
]
