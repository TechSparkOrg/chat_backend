# accounts/serializers.py
from rest_framework import serializers
from .models import CustomUser
from django.db.models import Q

# Import your Message model (adjust the import path as needed)
from chat.models import Message




class UserSerializer(serializers.ModelSerializer):
    friend_status = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unseen_count = serializers.SerializerMethodField()
    chat_exists = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()  # Optional; if your user model has online info

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'name',
            'phone_number',
            'email',
            'friend_status',
            'last_message',
            'unseen_count',
            'chat_exists',
            'delivery_status',
            'online',
        )

    def get_friend_status(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if obj in request.user.contacts.all():
                return "friend"
        return "unknown"

    def get_last_message(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        logged_in_user = request.user
        # Query messages between the logged in user and this user, ordered by timestamp descending.
        last_msg = Message.objects.filter(
            Q(sender=logged_in_user, recipient=obj) | Q(sender=obj, recipient=logged_in_user)
        ).order_by('-timestamp').first()
        return last_msg.text if last_msg else None

    def get_unseen_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        logged_in_user = request.user
        # Count messages sent by obj to the logged in user that are not marked as "read".
        count = Message.objects.filter(
            sender=obj,
            recipient=logged_in_user
        ).exclude(status='read').count()
        return count

    def get_chat_exists(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        logged_in_user = request.user
        return Message.objects.filter(
            Q(sender=logged_in_user, recipient=obj) | Q(sender=obj, recipient=logged_in_user)
        ).exists()

    def get_delivery_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return ""
        logged_in_user = request.user
        # Get the latest message in either direction.
        last_msg = Message.objects.filter(
            Q(sender=logged_in_user, recipient=obj) | Q(sender=obj, recipient=logged_in_user)
        ).order_by('-timestamp').first()
        return last_msg.status if last_msg else ""

    def get_online(self, obj):
        # If your CustomUser model has an 'online' field, return that; otherwise, return False.
        return getattr(obj, 'online', False)
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
