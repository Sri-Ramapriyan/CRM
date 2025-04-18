# chat/context_processors.py
from chat.models import Message
from collections import defaultdict

def unread_message_count(request):
    if request.user.is_authenticated:
        unread_messages = Message.objects.filter(receiver=request.user, read=False)
        total_unread = unread_messages.count()

        per_sender = defaultdict(int)
        for msg in unread_messages:
            per_sender[msg.sender.username] += 1

        return {
            'unread_message_total': total_unread,
            'unread_messages_by_sender': dict(per_sender)
        }
    return {}
