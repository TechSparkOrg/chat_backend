# chat/urls.py
from django.urls import path
from .views import conversation_messages, conversation_summary

urlpatterns = [
    path('messages/', conversation_messages, name='conversation_messages'),
    path('conversationuserlist/', conversation_summary, name='conversation_summary'),
]
