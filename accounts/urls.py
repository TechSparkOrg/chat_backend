# accounts/urls.py
from django.urls import path
from .views import RegisterView, LoginView, UserListView, UserSearchView, AddContactView, ContactListView,LogoutView, ConversationUserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('contacts/add/', AddContactView.as_view(), name='add-contact'),
    path('contacts/', ContactListView.as_view(), name='contact-list'),
    path('logout/', LogoutView.as_view(), name='contact-lists'),
    path('conversation-users/', ConversationUserListView.as_view(), name='conversation_users')
]
