from django.urls import path, include
import conversation.views as views

urlpatterns = [
    path('create_conversation', views.create_conversation),
    path('pull_conversation_list', views.pull_conversation_list),
    path('pull_conversation_chain', views.pull_conversation_chain),
    path('pull_conversation_member_list', views.pull_conversation_member_list),
    path('pull_conversation_chain_history', views.pull_conversation_chain_history),
    path('appoint_admin', views.appoint_admin),
    path('transfer_ownership', views.transfer_ownership),
    path('quit_conversation', views.quit_conversation),
    path('remove_member', views.remove_member),
    path('invite_new_member', views.invite_new_member),
    path('pull_conversation_apply_chain', views.pull_conversation_apply_chain),
    path('handle_conversation_apply', views.handle_conversation_apply),
    path("pull_announcement", views.pull_announcement),
    path("put_announcement", views.put_announcement)
]