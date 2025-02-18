# chat/views.py
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Message
from .serializers import MessageSerializer, ConversationSummarySerializer

from urllib.parse import urlencode
from django.urls import reverse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_messages(request):
    contact_id = request.query_params.get('contact_id', '').strip()
    contact_id = contact_id.replace('“', '').replace('”', '')  # Remove smart quotes

    if not contact_id:
        return Response({"error": "contact_id parameter is required."}, status=400)
    
    user = request.user
    
    # Fetch messages between user and selected contact
    messages_qs = Message.objects.filter(
        Q(sender=user, recipient__id=contact_id) |
        Q(sender__id=contact_id, recipient=user)
    ).order_by('-timestamp')  # Latest messages first

    # Pagination
    page = request.query_params.get('page', 1)  # Default to first page
    paginator = Paginator(messages_qs, 10)  # 10 messages per page

    try:
        page = int(page)  # Ensure page is an integer
        messages_paginated = paginator.page(page)
    except (PageNotAnInteger, ValueError, EmptyPage):  
        # If page is not valid, return first page
        messages_paginated = paginator.page(1)

    serializer = MessageSerializer(messages_paginated.object_list, many=True)

    base_url = request.build_absolute_uri(reverse('conversation_messages'))  # Dynamic API URL

    # Construct next and previous page URLs
    query_params = {'contact_id': contact_id}
    
    next_url = (
        f"{base_url}?{urlencode({**query_params, 'page': page + 1})}"
        if messages_paginated.has_next() else None
    )
    
    prev_url = (
        f"{base_url}?{urlencode({**query_params, 'page': page - 1})}"
        if messages_paginated.has_previous() else None
    )

    return Response({
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
        "current_page": page,
        "next": next_url,
        "previous": prev_url,
        "results": serializer.data,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_summary(request):
    user = request.user
    all_msgs = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('timestamp')
    conversations = {}
    
    for msg in all_msgs:
        partner = msg.recipient if msg.sender == user else msg.sender
        partner_id = partner.id

        if partner_id not in conversations or msg.timestamp > conversations[partner_id]['last_timestamp']:
            conversations[partner_id] = {
                'partner_id': partner_id,
                'partner_name': getattr(partner, 'username', str(partner)),
                'last_message': msg.text,
                'last_timestamp': msg.timestamp,
                'unseen_count': 0,
            }
    
    for partner_id, conv in conversations.items():
        unseen = Message.objects.filter(
            sender__id=partner_id,
            recipient=user,
            status__in=['sent', 'delivered']
        ).count()
        conv['unseen_count'] = unseen

    conversations_list = list(conversations.values())
    conversations_list.sort(key=lambda conv: conv['last_timestamp'], reverse=True)

    serializer = ConversationSummarySerializer(conversations_list, many=True)
    return Response(serializer.data)
