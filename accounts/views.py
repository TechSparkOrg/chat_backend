# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, LoginSerializer
from django.db.models import Q
from .models import CustomUser
import uuid
from chat.models import Message
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import login
from .models import CustomUser
from .serializers import UserSerializer

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        phone_number = data.get('phone_number')
       
        try:
            user = CustomUser.objects.create_user(
                email=email, 
                password=password,
                name=name,
                phone_number=phone_number
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Log in the user (set session/cookie)
        login(request, user)
        return Response({
            'message': 'Successfully Created',
            'status': 201
        }, status=status.HTTP_201_CREATED)



class LoginView(APIView):
    # Allow any user to attempt login.
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        logging.error('errro',serializer)
        logging.info('errro',serializer)
  
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            logging.info('userr',user)
            if user:
                # Log in the user (sets the session cookie)
                login(request, user)
                # Get or create the token for token authentication
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Logged in successfully.',
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'status': 200
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Please check your credentials and try again.','status': 400}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    # Only authenticated users can log out.
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Log out the user to clear the session cookie.
        logout(request)
        # Optionally, delete the token if you want to force a new token to be generated on next login.
        # Uncomment the following lines if token revocation on logout is desired:
        # try:
        #     request.user.auth_token.delete()
        # except Exception as e:
        #     print("Token deletion error:", e)
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    API view to retrieve the list of users.
    Only authenticated users can access this endpoint.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserSearchView(generics.ListAPIView):
    """
    API view to search for users by a generic query parameter 'q'
    that matches against id, name, or phone_number.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        query_value = self.request.query_params.get('q', None)

        if query_value:
            # Try filtering by UUID if possible
            uuid_filter = Q()
            try:
                uuid_obj = uuid.UUID(query_value)
                uuid_filter = Q(id=uuid_obj)
            except ValueError:
                pass

            combined_filter = (
                uuid_filter |
                Q(name__icontains=query_value) |
                Q(phone_number__icontains=query_value)
            )
            queryset = queryset.filter(combined_filter)

        return queryset
    

class AddContactView(APIView):
    """
    Add a contact for the logged-in user by providing a contact_id.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        contact_id = request.data
        if not contact_id:
            return Response({'error': 'contact_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            contact = CustomUser.objects.get(id=contact_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id == contact.id:
            return Response({'error': "You cannot add yourself as a contact."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the contact (if not already added)
        request.user.contacts.add(contact)
        serialized_contact = UserSerializer(contact, context={'request': request}).data
        return Response({
            'message': 'Contact added successfully',
            'contact': serialized_contact,
            'status': 200
        }, status=status.HTTP_200_OK)


class ContactListView(generics.ListAPIView):
    """
    Retrieve the list of contacts (friends) for the logged-in user,
    including the total number of contacts.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.contacts.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            "total_contacts": queryset.count(),
            "contacts": serializer.data,
        }
        return Response(response_data)

class ConversationUserListView(generics.ListAPIView):
    """
    Returns a list of users with whom the logged-in user has exchanged messages
    or who are in the user's contacts. Each user record includes conversation details,
    such as the last message, unseen count, and delivery_status.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Get IDs from messages where the user is the sender or recipient.
        sent_ids = Message.objects.filter(sender=user).values_list('recipient', flat=True)
        received_ids = Message.objects.filter(recipient=user).values_list('sender', flat=True)
        conversation_ids = set(list(sent_ids) + list(received_ids))
        
        # Also include the user's contacts.
        contact_ids = set(user.contacts.all().values_list('id', flat=True))
        
        # The union of both sets.
        final_ids = conversation_ids.union(contact_ids)
        final_ids.discard(user.id)  # Exclude self.
        
        return CustomUser.objects.filter(id__in=final_ids)
