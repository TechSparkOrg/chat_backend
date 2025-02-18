# chat/serializers.py
from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    # Optionally, you can represent the sender and recipient by their IDs.
    sender = serializers.UUIDField(source='sender.id')
    recipient = serializers.UUIDField(source='recipient.id')
    action_type=serializers.CharField(required=False)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'text', 'timestamp', 'status', 'media','action_type']
    
    def create(self, validated_data):
        # Remove the action_type value from the incoming data (if provided)
        action_type = validated_data.pop("action_type", None)
        # Create the Message instance using the remaining data.
        instance = super().create(validated_data)
        # Attach action_type as a temporary attribute (it won’t be saved to the DB)
        instance.action_type = action_type if action_type is not None else "message"
        return instance

    def to_representation(self, instance):
        # Get the default serialized data.
        data = super().to_representation(instance)
        # Add acticon_type to the representation (using the attached attribute or default "message")
        data["action_type"] = getattr(instance, "action_type", "message")
        return data
        
class ConversationSummarySerializer(serializers.Serializer):
    partner_id = serializers.UUIDField()
    partner_name = serializers.CharField()
    last_message = serializers.CharField()
    last_timestamp = serializers.DateTimeField()
    unseen_count = serializers.UUIDField()
 