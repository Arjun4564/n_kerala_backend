from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, LoginView
from . import views

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('search/', views.UserSearchView.as_view(), name='user_search'),
    
    # 🟢 1. Put the specific 'green' endpoint FIRST so Django doesn't confuse it for a username
    path('profile/<int:user_id>/green/', views.ToggleGreenView.as_view(), name='toggle_green'),
    
    # 🟢 2. Put the dynamic string endpoint LAST (Handles both ID numbers and Usernames safely)
    path('profile/<str:identifier>/', views.UserProfileView.as_view(), name='user_profile'),
    
    path('profile/update/bio/', views.UpdateProfileBioView.as_view(), name='update_bio'),
]