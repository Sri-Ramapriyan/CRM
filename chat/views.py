from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .models import Message
from .forms import MessageForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from datetime import timedelta


User = get_user_model()

@login_required
def inbox(request):
    logged_in_user = request.user
    search_query = request.GET.get('search', '').strip().lower()
    user_threads = []

    # CASE 1: Searching - show everyone matching the query (excluding yourself)
    if search_query:
        users = User.objects.exclude(id=logged_in_user.id).filter(username__icontains=search_query)

    # CASE 2: No search - only show users the current user has messaged with
    else:
        # Get all users the logged-in user has had a conversation with
        messaged_user_ids = Message.objects.filter(
            Q(sender=logged_in_user) | Q(receiver=logged_in_user)
        ).values_list('sender', 'receiver', named=True)

        # Flatten sender/receiver pairs and remove self
        user_ids = set()
        for pair in messaged_user_ids:
            if pair.sender != logged_in_user.id:
                user_ids.add(pair.sender)
            if pair.receiver != logged_in_user.id:
                user_ids.add(pair.receiver)

        users = User.objects.filter(id__in=user_ids)

    for user in users:
        # Last message between current user and the other user
        last_message = Message.objects.filter(
            Q(sender=logged_in_user, receiver=user) |
            Q(sender=user, receiver=logged_in_user)
        ).order_by('-timestamp').first()

        # If no message, show bottom (datetime.min) — only happens during search
        last_time = last_message.timestamp if last_message else datetime.min

        if timezone.is_naive(last_time):
            last_time = timezone.make_aware(last_time, timezone.get_current_timezone())

        unread_count = Message.objects.filter(
            sender=user,
            receiver=logged_in_user,
            read=False
        ).count()

        user_threads.append({
            'user': user,
            'last_message': last_message,
            'last_message_time': last_time,
            'unread_count': unread_count,
        })

    # Sort by latest message time
    sorted_users = sorted(user_threads, key=lambda u: u['last_message_time'], reverse=True)

    return render(request, 'chat/inbox.html', {
        'sorted_users': sorted_users,
        'search_query': search_query,
    })


@login_required
def chat_view(request, username):
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('chat:inbox')

    # mark unread as read
    Message.objects.filter(
        sender=other_user, 
        receiver=request.user, 
        read=False
    ).update(read=True)

    # fetch the two-way conversation
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save(sender=request.user, receiver=other_user)
            return redirect('chat:chat', username=username)
    else:
        form = MessageForm(initial={'receiver_username': username})

    # add today / yesterday
    today     = timezone.localdate()
    yesterday = today - timedelta(days=1)

    return render(request, 'chat/chat.html', {
        'messages': messages,
        'form':     form,
        'receiver': other_user,
        'today':    today,
        'yesterday': yesterday,
    })
def chat(request, username):
    logged_in_user = request.user
    user = User.objects.get(username=username)

    # Fetch messages between the logged-in user and the other user
    messages = Message.objects.filter(
        (Q(sender=logged_in_user) & Q(receiver=user)) |
        (Q(sender=user) & Q(receiver=logged_in_user))
    )

    # Mark messages as read for the logged-in user
    messages.filter(receiver=logged_in_user, read=False).update(read=True)

    return render(request, 'chat/chat.html', {'messages': messages, 'user': user})


def get_unread_count(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})