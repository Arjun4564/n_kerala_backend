from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import UserProfile

# 🟢 1. Import your core models
from .models import (
    Topic, Opinion, OpinionLike, OpinionBoost, OpinionReply,
    Report, AvasthaMood, Battle, BattleVote, UserBadge,
    Notification, BattleArena, BattleOption, BattleArenaVote, Badge
)



User = get_user_model()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def user_is_banned(user):
    if hasattr(user, "currently_banned"):
        return user.currently_banned()
    return getattr(user, "is_banned", False)

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

def user_short_data(user):
    full_name = user.get_full_name().strip()
    profile = get_or_create_profile(user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name": full_name if full_name else user.username,
        "bio": profile.bio,
        "profile_picture": profile.profile_picture.url if profile.profile_picture else None,
        "is_subscriber": profile.is_subscriber,
        "is_verified": user.is_superuser or user.is_staff or getattr(user, "is_verified", False) or profile.is_subscriber,
        "is_owner": False,
    }

def opinion_data(opinion, request):
    full_name = opinion.user.get_full_name().strip()
    profile = get_or_create_profile(opinion.user)
    
    is_liked = False
    is_boosted = False
    is_owner = False
    
    if request.user.is_authenticated:
        is_owner = (opinion.user == request.user)
        is_liked = OpinionLike.objects.filter(user=request.user, opinion=opinion).exists()
        is_boosted = OpinionBoost.objects.filter(user=request.user, opinion=opinion).exists()

    return {
        "id": opinion.id,
        "username": opinion.user.username,
        "full_name": full_name if full_name else opinion.user.username,
        "profile_picture": profile.profile_picture.url if profile.profile_picture else None,
        "is_subscriber": profile.is_subscriber,
        "is_owner": is_owner,
        "topic": opinion.topic.id,
        "topic_title": opinion.topic.title,
        "content": opinion.content,
        "like_count": opinion.like_count,
        "reply_count": opinion.reply_count,
        "boost_count": opinion.boost_count,
        "view_count": opinion.view_count,
        "share_count": opinion.share_count,
        "is_liked": is_liked,
        "is_boosted": is_boosted,
        "created_at": opinion.created_at,
    }

# ==========================================
# FEEDS & OPINIONS
# ==========================================
class TopicListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 🟢 1. THE AUTO-SEED FAILSAFE
        if not Topic.objects.exists():
            default_topics = ['Sports','Movies','Politics','Education','Business','Technology','Health','Entertainment','Lifestyle','Others']
            for title in default_topics:
                # Creates them instantly if the database is empty
                Topic.objects.create(title=title, description="Default category", is_active=True)

        # 🟢 2. NORMAL FETCHING LOGIC
        topics = Topic.objects.filter(is_active=True)
        data = []

        for topic in topics:
            opinions = Opinion.objects.filter(topic=topic, is_deleted=False)
            opinion_count = opinions.count()
            like_total = sum(op.like_count for op in opinions)
            boost_total = sum(op.boost_count for op in opinions)
            engagement_score = opinion_count + like_total + boost_total

            data.append({
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "opinion_count": opinion_count,
                "engagement_score": engagement_score,
                "created_at": topic.created_at,
            })

        data.sort(key=lambda x: x["engagement_score"], reverse=True)
        return Response(data)

class OpinionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        feed_type = request.GET.get("type", "all")
        opinions = Opinion.objects.filter(is_deleted=False).select_related("user", "topic")

        if feed_type == "top":
            opinions = opinions.order_by("-boost_count", "-created_at")[:50]
        else:
            opinions = sorted(
                opinions,
                key=lambda op: (not get_or_create_profile(op.user).is_subscriber, -op.created_at.timestamp())
            )

        data = [opinion_data(opinion, request) for opinion in opinions]
        return Response(data)

    def post(self, request):
        if user_is_banned(request.user):
            return Response({"message": "Your account is banned"}, status=status.HTTP_403_FORBIDDEN)

        topic_id = request.data.get("topic")
        content = request.data.get("content", "").strip()

        if not topic_id:
            return Response({"message": "Topic is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({"message": "Opinion cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        if len(content) > 120:
            return Response({"message": "Opinion max 120 characters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
        except Topic.DoesNotExist:
            return Response({"message": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)

        opinion = Opinion.objects.create(user=request.user, topic=topic, content=content)
        return Response(opinion_data(opinion, request), status=status.HTTP_201_CREATED)

class EditOpinionView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, opinion_id):
        content = request.data.get("content", "").strip()

        if not content:
            return Response({"message": "Opinion cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            opinion = Opinion.objects.get(id=opinion_id, user=request.user, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        opinion.content = content
        opinion.save(update_fields=["content"])
        return Response({"message": "Opinion updated", "opinion": opinion_data(opinion, request)})

class DeleteOpinionView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, opinion_id):
        try:
            opinion = Opinion.objects.get(id=opinion_id, user=request.user, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        opinion.is_deleted = True
        opinion.deleted_at = timezone.now()
        opinion.save(update_fields=["is_deleted", "deleted_at"])
        return Response({"message": "Opinion deleted"})

class LikeOpinionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, opinion_id):
        try:
            opinion = Opinion.objects.get(id=opinion_id, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        like, created = OpinionLike.objects.get_or_create(user=request.user, opinion=opinion)

        if created:
            opinion.refresh_from_db()
            return Response({"is_liked": True, "like_count": opinion.like_count})

        like.delete()
        opinion.refresh_from_db()
        return Response({"is_liked": False, "like_count": opinion.like_count})

class OpinionBoostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, opinion_id):
        today = timezone.now().date()
        daily_count = OpinionBoost.objects.filter(user=request.user, created_at__date=today).count()

        if daily_count >= 2:
            return Response({"message": "Daily boost limit reached"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            opinion = Opinion.objects.get(id=opinion_id, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        already_boosted = OpinionBoost.objects.filter(user=request.user, opinion=opinion).exists()
        if already_boosted:
            return Response({"message": "Already boosted"}, status=status.HTTP_400_BAD_REQUEST)

        OpinionBoost.objects.create(user=request.user, opinion=opinion)
        opinion.refresh_from_db()
        return Response({"message": "Opinion boosted", "boost_count": opinion.boost_count})

class BoostStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        used = OpinionBoost.objects.filter(user=request.user, created_at__date=today).count()

        return Response({
            "daily_limit": 2,
            "used_boosts": used,
            "remaining_boosts": max(2 - used, 0),
        })

class OpinionReplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, opinion_id):
        try:
            opinion = Opinion.objects.get(id=opinion_id, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        replies = OpinionReply.objects.filter(opinion=opinion, is_deleted=False).select_related("user").order_by("created_at")
        data = []

        for reply in replies:
            profile = get_or_create_profile(reply.user)
            data.append({
                "id": reply.id,
                "username": reply.user.username,
                "full_name": reply.user.get_full_name().strip() or reply.user.username,
                "profile_picture": profile.profile_picture.url if profile.profile_picture else None,
                "is_subscriber": profile.is_subscriber,
                "content": reply.content,
                "created_at": reply.created_at,
            })
        return Response(data)

    def post(self, request, opinion_id):
        content = request.data.get("content", "").strip()

        if not content:
            return Response({"message": "Comment cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            opinion = Opinion.objects.get(id=opinion_id, is_deleted=False)
        except Opinion.DoesNotExist:
            return Response({"message": "Opinion not found"}, status=status.HTTP_404_NOT_FOUND)

        reply = OpinionReply.objects.create(user=request.user, opinion=opinion, content=content)
        opinion.refresh_from_db()

        return Response({
            "id": reply.id,
            "content": reply.content,
            "reply_count": opinion.reply_count,
        })

# ==========================================
# NOTIFICATIONS & REPORTS
# ==========================================
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        notifs = Notification.objects.filter(user=request.user, is_deleted=False).order_by('-created_at')
        data = [{
            "id": n.id, "title": getattr(n, 'title', 'Notification'),
            "message": getattr(n, 'message', getattr(n, 'content', '')),
            "notification_type": getattr(n, 'notification_type', getattr(n, 'type', 'general')),
            "is_read": getattr(n, 'is_read', False),
            "created_at": n.created_at.isoformat() if getattr(n, 'created_at', None) else None,
        } for n in notifs]
        return Response(data)

class TrashNotificationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        trashed = Notification.objects.filter(user=request.user, is_deleted=True).order_by('-deleted_at')
        data = [{
            "id": n.id, "title": getattr(n, 'title', 'Notification'),
            "message": getattr(n, 'message', getattr(n, 'content', '')),
            "deleted_at": n.deleted_at.isoformat() if getattr(n, 'deleted_at', None) else None,
        } for n in trashed]
        return Response(data)

class DeleteNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        notif = Notification.objects.filter(id=pk, user=request.user).first()
        if notif:
            notif.is_deleted = True
            notif.deleted_at = timezone.now()
            notif.save()
            return Response({"success": True})
        return Response({"success": False}, status=404)

class RestoreNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        notif = Notification.objects.filter(id=pk, user=request.user).first()
        if notif:
            notif.is_deleted = False
            notif.deleted_at = None
            notif.save()
            return Response({"success": True})
        return Response({"success": False}, status=404)

class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False, is_deleted=False).count()
        return Response({"unread_count": count})

class MarkSingleNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        notif = Notification.objects.filter(id=pk, user=request.user).first()
        if notif:
            notif.is_read = True
            notif.save()
        return Response({"success": True})

class ReportCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"message": "Report submitted"})

# ==========================================
# BATTLE ARENA & MISC
# ==========================================
class BattleArenaCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        question = data.get("question")
        battle_type = data.get("battle_type")  # "one_vs_one" or "four_option"
        is_urgent = data.get("is_urgent", False)
        options_data = data.get("options", [])  # Expects list of strings: ["Option A", "Option B"]

        # 1. Validation checks
        if not question or not battle_type or not options_data:
            return Response(
                {"error": "Missing required fields: question, battle_type, and options are mandatory."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if battle_type == "one_vs_one" and len(options_data) != 2:
            return Response({"error": "1 vs 1 battles must have exactly 2 choices."}, status=status.HTTP_400_BAD_REQUEST)
        
        if battle_type == "four_option" and len(options_data) != 4:
            return Response({"error": "4 Option battles must have exactly 4 choices."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Establish timelines (e.g., battle expires in 24 hours, or 4 hours if urgent)
            duration = timedelta(hours=4) if is_urgent else timedelta(days=1)
            now = timezone.now()
            ends_at = now + duration

            # 3. Create the parent Battle Arena item
            battle = BattleArena.objects.create(
                creator=request.user,
                battle_type=battle_type,
                question=question,
                is_urgent=is_urgent,
                status="active",
                ends_at=ends_at
            )

            # 4. Create bulk entries for choices attached to this game instance
            for option_text in options_data:
                BattleOption.objects.create(
                    battle=battle,
                    text=option_text
                )

            return Response(
                {
                    "message": "Battle created successfully",
                    "battle_id": battle.id
                }, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BattleArenaListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Read a 'filter' query param from Flutter (e.g., /api/battles/?filter=created)
        filter_type = request.query_params.get('filter', 'active')
        user = request.user

        # 1. Base QuerySet
        queryset = BattleArena.objects.all()

        # 2. Apply filtering based on what Tab your Flutter UI is asking for
        if filter_type == 'created':
            # Returns battles created by the logged-in user
            queryset = queryset.filter(creator=user)
        elif filter_type == 'result':
            # Returns completed battles showing winners
            queryset = queryset.filter(status__in=['glow', 'result'])
        else:
            # Default fallback: show active ongoing debates
            queryset = queryset.filter(status='active')

        # 3. Serialize data structure manually to match your custom options array
        battles_list = []
        for battle in queryset:
            # Collect choices for each battle item
            options = [
                {
                    "id": opt.id,
                    "text": opt.text,
                    "vote_count": opt.vote_count,
                    "is_winner": opt.is_winner
                }
                for opt in battle.options.all()
            ]

            # Check if the current user already voted in this specific battle
            user_vote = BattleArenaVote.objects.filter(user=user, battle=battle).first()
            has_voted = user_vote is not None
            voted_option_id = user_vote.option.id if has_voted else None

            battles_list.append({
                "id": battle.id,
                "question": battle.question,
                "battle_type": battle.battle_type,
                "status": battle.status,
                "is_urgent": battle.is_urgent,
                "creator_id": battle.creator.id,
                "ends_at": battle.ends_at.isoformat(),
                "created_at": battle.created_at.isoformat(),
                "has_voted": has_voted,
                "voted_option_id": voted_option_id,
                "options": options
            })

        return Response({"battles": battles_list}, status=status.HTTP_200_OK)
class BattleArenaVoteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, battle_id):
        return Response({"message": "Vote submitted", "battle_id": battle_id})
    
class SubmitFeedbackView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        message = request.data.get("message", "").strip()
        if not message:
            return Response({"message": "Message is empty"}, status=status.HTTP_400_BAD_REQUEST)
        print(f"🔥 NEW FEEDBACK from {request.user.username}: {message}")
        return Response({"message": "Feedback received"}, status=status.HTTP_200_OK)