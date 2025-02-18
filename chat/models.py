# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')  # e.g. sent, delivered, read
    media = models.JSONField(blank=True, null=True)  # For any attached media (if needed)

    def __str__(self):
        return f'Message from {self.sender} to {self.recipient} at {self.timestamp}'
