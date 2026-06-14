from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from .models import Follow, UserProfile
from django.utils.timesince import timesince
from core.models import Opinion, OpinionBoost





User = get_user_model()




class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        # 1. Validation
        if not username or not password or not email:
            return Response({"message": "Username, email, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username__iexact=username).exists():
            return Response({"message": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email__iexact=email).exists():
            return Response({"message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. User Creation (Profile is auto-created by the Signal we added earlier!)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 3. Generate Play Store Ready JWTs
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Account created successfully.",
            "token": str(refresh.access_token),  # Labeled 'token' for Flutter compatibility
            "refresh_token": str(refresh),
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        # 1. Authenticate
        user = authenticate(username=username, password=password)

        if user is None:
            return Response({"message": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # 2. Ban Check
        if hasattr(user, 'currently_banned') and user.currently_banned():
            return Response({"message": f"Account banned. Reason: {user.ban_reason}"}, status=status.HTTP_403_FORBIDDEN)

        # 3. Generate Play Store Ready JWTs
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful.",
            "token": str(refresh.access_token),  # Labeled 'token' for Flutter compatibility
            "refresh_token": str(refresh),
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_200_OK)
        


User = get_user_model()

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()

        if not query:
            # 🟢 THE VIRAL ENGINE
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            # 👻 THE FIX: Added .exclude(is_superuser=True) to hide admins from Trending
            trending_users = User.objects.exclude(
                id=request.user.id
            # ).exclude(
            #     is_superuser=True 
            ).annotate(
                new_greens=Count(
                    'followers', # (Change this if your related_name is different)
                    filter=Q(followers__created_at__gte=one_hour_ago)
                )
            ).filter(new_greens__gt=0).order_by('-new_greens')[:5]

            users_list = list(trending_users)

            # 🟢 THE FALLBACK
            if len(users_list) < 5:
                slots_to_fill = 5 - len(users_list)
                trending_ids = [u.id for u in users_list] 
                
                # 👻 THE FIX: Added .exclude(is_superuser=True) to hide admins from Fallbacks
                fallback_users = User.objects.exclude(
                    id=request.user.id
                ).exclude(
                    id__in=trending_ids
                # ).exclude(
                #     is_superuser=True
                ).order_by('-last_login')[:slots_to_fill]
                
                users_list.extend(fallback_users)
                
            users = users_list 
        
        else:
            # 🟢 THE REAL SEARCH ENGINE
            search_engine = (
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            
            # 👻 THE FIX: Added .exclude(is_superuser=True) to hide admins from search results!
            # Note: You can still search for yourself as long as your account isn't a superuser.
            users = User.objects.filter(search_engine)
            # .exclude(is_superuser=True)[:50]

        # Format the data for Flutter
        data = []
        for u in users:
            full_name = f"{u.first_name} {u.last_name}".strip()
            if not full_name:
                full_name = u.username

            data.append({
                "id": u.id,
                "username": u.username,
                "full_name": full_name,
                "email": u.email,
            })

        return Response(data)
    


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # 🟢 CHANGED: Accept 'identifier' instead of 'user_id'
    def get(self, request, identifier):
        
        # 🟢 THE FIX: Check if Flutter sent an ID (digits) or a Username (letters)
        if str(identifier).isdigit():
            user = get_object_or_404(User, id=identifier)
        else:
            user = get_object_or_404(User, username__iexact=identifier)

        is_self = (request.user.id == user.id)

        full_name = f"{user.first_name} {user.last_name}".strip()
        if not full_name:
            full_name = user.username
            
        is_verified = user.is_superuser or user.is_staff or getattr(user, 'is_subscriber', False)

        is_greened = False
        if not is_self:
            is_greened = Follow.objects.filter(follower=request.user, followed=user).exists()

        # 🟢 1. THE GLOBAL TRENDING ENGINE (Cleaned up the old 30-min logic)
        trending_ids = Opinion.objects.filter(
            is_deleted=False
        ).order_by('-boost_count', '-created_at').values_list('id', flat=True)[:50]
        
        # Counts how many of THIS user's opinions are currently sitting in that global Top 50 pool
        trend_count = Opinion.objects.filter(user=user, id__in=trending_ids).count()

        # 🟢 2. THE OPINIONS ENGINE
        # 🟢 2. THE OPINIONS ENGINE
        # 🟢 THE FIX: Added is_deleted=False to hide the soft-deleted opinions!
        opinions_db = Opinion.objects.filter(user=user, is_deleted=False).order_by('-created_at')
        opinions_list = []
        for op in opinions_db:
            opinions_list.append({
                "id": op.id,
                "text": op.content,  # Points directly to your core model's content field
                "time_ago": f"{timesince(op.created_at)} ago",
                "total_boosts": op.boost_count, 
            })

        # 🟢 3. PACKAGE THE DATA
        data = {
            "id": user.id,
            "username": user.username,
            "full_name": full_name,
            "email": user.email,
            "is_self": is_self,
            "date_joined": user.date_joined.strftime("%B %Y"),
            "is_verified": is_verified,
            
            # 🟢 THE FIX: We must actually tell Flutter what the bio is!
            "bio": user.profile.bio if hasattr(user, 'profile') else "",
            
            # The profile picture URL (if you added the field to your user/profile model)
            # "profile_picture": user.profile.profile_picture.url if getattr(user, 'profile', None) and user.profile.profile_picture else None,
            
            "is_greened": is_greened,
            "greens_count": user.followers.count(), 
            "raids_count": user.following.count(), 
            "trend_count": trend_count, 
            
            "badges": [],
            "opinions": opinions_list, 
        }

        return Response(data)


class ToggleGreenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user == request.user:
            return Response({"error": "You cannot green yourself."}, status=400)

        follow = Follow.objects.filter(follower=request.user, followed=target_user).first()

        if follow:
            follow.delete()
            is_greened = False
        else:
            Follow.objects.create(follower=request.user, followed=target_user)
            is_greened = True

        return Response({
            "is_greened": is_greened,
            "greens_count": target_user.followers.count(), 
            "raids_count": target_user.following.count(), # 🟢 FIX: Update RAIDS live!
            "trend_count": 0, 
        })
        
class UpdateProfileBioView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        
        # 1. Get the data from Flutter
        full_name = request.data.get('full_name', '').strip()
        bio = request.data.get('bio', '').strip()

        # 2. Update the User Model (Name)
        if full_name:
            # Split the full name into first and last name for Django
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.save()

        # 3. Update the UserProfile Model (Bio)
        # Ensure the profile exists just in case the signal failed on older accounts
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.bio = bio
        profile.save()

        return Response({
            "message": "Profile updated successfully.",
            "full_name": full_name,
            "bio": bio
        }, status=status.HTTP_200_OK)
        
        

