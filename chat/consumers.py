# chat/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"Scope headers: {self.scope.get('headers')}")
        logger.info(f"Scope cookies: {self.scope.get('cookies')}")
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Each authenticated user joins their own group.
        self.group_name = f"chat_{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"User {self.user.id} connected.")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        logger.info(f"User {self.user.id} disconnected.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action_type = data.get('action_type', 'message')
        
        if action_type == 'delivery_status':
            message_id = data.get('id')
            new_status = data.get('status')
            updated_message = await self.update_message_status(message_id, new_status)
            if updated_message:
                # Serialize the updated message in a sync context.
                message_data = await self.serialize_message(updated_message, action_type='delivery_status')
                recipient_group = f"chat_{message_data['to']}"
                await self.channel_layer.group_send(
                    recipient_group,
                    {
                        'type': 'chat.message',
                        'message': message_data
                    }
                )
                await self.send(text_data=json.dumps(message_data))
            else:
                logger.error("Message not found for delivery status update.")
        elif action_type == 'typing':
            # For typing events, simply broadcast the event.
            const_recipient_id = data.get('to') or data.get('recipient')
            message_data = {
                'action_type': 'typing',
                'typing': data.get('typing', False),
                'from': data.get('from'),
                'to': const_recipient_id
            }
            recipient_group = f"chat_{const_recipient_id}"
            await self.channel_layer.group_send(
                recipient_group,
                {
                    'type': 'chat.message',
                    'message': message_data
                }
            )
        else:
            # Default: create a new message.
            sender_id = str(self.user.id)
            const_recipient_id = data.get('to') or data.get('recipient')
            if not const_recipient_id:
                logger.error("Recipient id missing in the payload.")
                return
            text = data.get('text', '')
            status = data.get('status', 'sent')
            media = data.get('media', None)
            new_message = await self.create_message(sender_id, const_recipient_id, text, status, media)
            if new_message is None:
                logger.error("Failed to create message: user not found.")
                return
            message_data = await self.serialize_message(new_message, action_type='message')
            recipient_group = f"chat_{const_recipient_id}"
            await self.channel_layer.group_send(
                recipient_group,
                {
                    'type': 'chat.message',
                    'message': message_data
                }
            )
            await self.send(text_data=json.dumps(message_data))

    async def chat_message(self, event):
        message_data = event['message']
        await self.send(text_data=json.dumps(message_data))

    @database_sync_to_async
    def create_message(self, sender_id, recipient_id, text, status, media):
        try:
            sender = User.objects.get(id=sender_id)
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist as e:
            logger.error(f"User not found: {e} (sender_id: {sender_id}, recipient_id: {recipient_id})")
            return None
        return Message.objects.create(
            sender=sender,
            recipient=recipient,
            text=text,
            status=status,
            media=media
        )

    @database_sync_to_async
    def update_message_status(self, message_id, new_status):
        try:
            msg = Message.objects.get(id=message_id)
            msg.status = new_status
            msg.save()
            return msg
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def serialize_message(self, message, action_type='message'):
        """
        Serializes a message instance into a dictionary, ensuring that related fields
        are evaluated in a synchronous context.
        """
        return {
            'id': message.id,
            'from': str(message.sender.id),
            'to': str(message.recipient.id),
            'text': message.text,
            'timestamp': message.timestamp.isoformat(),
            'status': message.status,
            'media': message.media,
            'action_type': action_type
        }
