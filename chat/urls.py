from django.urls import path
from . import views
from .views import get_unread_count

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<str:username>/', views.chat_view, name='chat'),
    path('unread-count/', get_unread_count, name='unread-count'),
]