import re
import json
from datetime import datetime, timezone
from typing import Dict, Any
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message, Conversation

# Create your views here.
@require_http_methods(["POST", "GET"])
def messages(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        sender_username = data.get('username')
        content = data.get('content', '')

        # 验证 conversation_id 和 sender_username 的合法性
        try:
            conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)

        try:
            sender = User.objects.get(username=sender_username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid username'}, status=400)

        # 验证 sender 是否是 conversation 的成员
        if not conversation.members.filter(id=sender.id).exists():
            return JsonResponse({'error': 'Sender is not a member of the conversation'}, status=403)

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )

        message.receivers.set(conversation.members.all())

        channel_layer = get_channel_layer()
        for member in conversation.members.all():
            async_to_sync(channel_layer.group_send)(member.username, {'type': 'notify'})

        return JsonResponse(format_message(message), status=200)

    elif request.method == "GET":
        username: str = request.GET.get('username')
        conversation_id: str = request.GET.get('conversation_id')
        after: str = request.GET.get('after', '0')
        after_datetime = datetime.fromtimestamp((int(after) + 1) / 1000.0, tz=timezone.utc)
        limit: int = int(request.GET.get('limit', '100'))

        messages_query = Message.objects.filter(timestamp__gte=after_datetime).order_by('timestamp')
        messages_query = messages_query.prefetch_related('conversation')

        if username:
            try:
                user = User.objects.get(username=username)
                messages_query = messages_query.filter(receivers=user)
            except User.DoesNotExist:
                return JsonResponse({'messages': [], 'has_next': False}, status=200)
        elif conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                messages_query = messages_query.filter(conversation=conversation)
            except Conversation.DoesNotExist:
                return JsonResponse({'messages': [], 'has_next': False}, status=200)
        else:
            return JsonResponse({'error': 'Either username or conversation ID must be specified'}, status=400)
        
        messages = list(messages_query[:limit+1])
        messages_data = [format_message(message) for message in messages]

        # 检查是否还有更多消息
        has_next = False
        if len(messages_data) > limit:
            has_next = True
            messages_data = messages_data[:limit]

        return JsonResponse({'messages': messages_data, 'has_next': has_next}, status=200)

@require_http_methods(["POST", "GET"])
def conversations(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        conversation_type = data.get('type')
        member_usernames = data.get('members', [])

        # 检查用户名是否合法
        members = []
        for username in member_usernames:
            if not check_username(username):
                return JsonResponse({'error': f'Invalid username: {username}'}, status=400)
            user, _ = User.objects.get_or_create(username=username)
            members.append(user)

        if not members:
            return JsonResponse({'error': f'Invalid member count'}, status=400)
        
        if conversation_type == 'private_chat':
            if len(members) != 2:
                return JsonResponse({'error': f'Invalid member count'}, status=400)
            # 检查是否已存在私人聊天
            existing_conversations = Conversation.objects.filter(members__in=members, type='private_chat').prefetch_related('members').distinct()
            for conv in existing_conversations:
                if conv.members.count() == 2 and set(conv.members.all()) == set(members):
                    # 找到了一个已存在的私人聊天，直接返回
                    return JsonResponse(format_conversation(conv), status=200)

        conversation = Conversation.objects.create(type=conversation_type)
        conversation.members.set(members)
        return JsonResponse(format_conversation(conversation), status=200)

    elif request.method == "GET":
        conversation_ids = request.GET.getlist('id', [])
        valid_conversations = Conversation.objects.filter(id__in=conversation_ids).prefetch_related('members')
        response_data = [format_conversation(conv) for conv in valid_conversations]
        return JsonResponse({'conversations': response_data}, status=200)

@require_http_methods(["POST"])
def join_conversation(request: HttpRequest, conversation_id: int) -> HttpResponse:
    data = json.loads(request.body)
    username = data.get('username')

    # 验证 conversation_id 和 username 的合法性
    try:
        conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Invalid conversation ID'}, status=404)

    if conversation.type == 'private_chat':
        return JsonResponse({'error': 'Unable to join private chat'}, status=403)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid username'}, status=404)
    
    conversation.members.add(user)

    return JsonResponse({'result': 'success'}, status=200)

@require_http_methods(["POST"])
def leave_conversation(request: HttpRequest, conversation_id: int) -> HttpResponse:
    data = json.loads(request.body)
    username = data.get('username')

    # 验证 conversation_id 和 username 的合法性
    try:
        conversation = Conversation.objects.prefetch_related('members').get(id=conversation_id) 
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Invalid conversation ID'}, status=404)

    if conversation.type == 'private_chat':
        return JsonResponse({'error': 'Unable to leave private chat'}, status=403)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid username'}, status=404)
    
    conversation.members.remove(user)

    return JsonResponse({'result': 'success'}, status=200)

def to_timestamp(dt: datetime) -> int:
    # 转换为毫秒级 UNIX 时间戳
    return int(dt.timestamp() * 1_000)

def format_message(message: Message) -> dict:
    return {
        'id': message.id,
        'conversation': message.conversation.id,
        'sender': message.sender.username,
        'content': message.content,
        'timestamp': to_timestamp(message.timestamp)
    }

def format_conversation(conversation: Conversation) -> dict:
    return {
        'id': conversation.id,
        'type': conversation.type,
        'members': [user.username for user in conversation.members.all()],
    }

def check_username(value: str) -> bool:
    return re.match(r'^\w+$', value) and len(value) <= 20