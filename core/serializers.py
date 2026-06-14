from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Topic,
    Opinion,
    OpinionLike,
    OpinionBoost,
    OpinionReply,
    Report,
    AvasthaMood,
    Battle,
    BattleVote,
    Badge,
    UserBadge,
    Green,
    UserProfile,
    BattleArena,
    BattleOption,
    BattleArenaVote,
    Notification,
)

User = get_user_model()


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic

        fields = [
            'id',
            'title',
            'description',
            'is_active',
            'created_at',
        ]


class OpinionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    district = serializers.CharField(
        source='user.district',
        read_only=True
    )

    profile_picture = serializers.ImageField(
        source='user.profile.profile_picture',
        read_only=True
    )

    is_liked = serializers.SerializerMethodField()

    is_boosted = serializers.SerializerMethodField()

    class Meta:
        model = Opinion

        fields = [
            'id',
            'username',
            'district',
            'profile_picture',
            'topic',
            'content',
            'like_count',
            'reply_count',
            'boost_count',
            'view_count',
            'share_count',
            'trending_score',
            'is_liked',
            'is_boosted',
            'created_at',
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return OpinionLike.objects.filter(
                user=request.user,
                opinion=obj
            ).exists()

        return False

    def get_is_boosted(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return OpinionBoost.objects.filter(
                user=request.user,
                opinion=obj
            ).exists()

        return False


class OpinionReplySerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    profile_picture = serializers.ImageField(
        source='user.profile.profile_picture',
        read_only=True
    )

    class Meta:
        model = OpinionReply

        fields = [
            'id',
            'username',
            'profile_picture',
            'opinion',
            'content',
            'created_at',
        ]


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(
        source='reporter.username',
        read_only=True
    )

    reported_username = serializers.CharField(
        source='reported_user.username',
        read_only=True
    )

    class Meta:
        model = Report

        fields = [
            'id',
            'report_type',
            'reporter',
            'reporter_username',
            'reported_user',
            'reported_username',
            'opinion',
            'reason',
            'created_at',
        ]

        read_only_fields = [
            'created_at',
        ]


class AvasthaMoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvasthaMood

        fields = [
            'id',
            'mood',
            'date',
            'created_at',
        ]


class BattleSerializer(serializers.ModelSerializer):
    opinion_a_text = serializers.CharField(
        source='opinion_a.content',
        read_only=True
    )

    opinion_b_text = serializers.CharField(
        source='opinion_b.content',
        read_only=True
    )

    opinion_a_user = serializers.CharField(
        source='opinion_a.user.username',
        read_only=True
    )

    opinion_b_user = serializers.CharField(
        source='opinion_b.user.username',
        read_only=True
    )

    total_votes = serializers.SerializerMethodField()

    vote_a_percentage = serializers.SerializerMethodField()

    vote_b_percentage = serializers.SerializerMethodField()

    user_voted = serializers.SerializerMethodField()

    user_selected_opinion = serializers.SerializerMethodField()

    class Meta:
        model = Battle

        fields = [
            'id',
            'title',
            'opinion_a',
            'opinion_a_text',
            'opinion_a_user',
            'opinion_b',
            'opinion_b_text',
            'opinion_b_user',
            'vote_a_count',
            'vote_b_count',
            'total_votes',
            'vote_a_percentage',
            'vote_b_percentage',
            'user_voted',
            'user_selected_opinion',
            'start_time',
            'end_time',
            'status',
            'winner_opinion',
            'created_at',
        ]

    def get_total_votes(self, obj):
        return obj.vote_a_count + obj.vote_b_count

    def get_vote_a_percentage(self, obj):
        total = obj.vote_a_count + obj.vote_b_count

        if total == 0:
            return 0

        return round(
            (obj.vote_a_count / total) * 100,
            2
        )

    def get_vote_b_percentage(self, obj):
        total = obj.vote_a_count + obj.vote_b_count

        if total == 0:
            return 0

        return round(
            (obj.vote_b_count / total) * 100,
            2
        )

    def get_user_voted(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return BattleVote.objects.filter(
                battle=obj,
                user=request.user
            ).exists()

        return False

    def get_user_selected_opinion(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            vote = BattleVote.objects.filter(
                battle=obj,
                user=request.user
            ).first()

            return vote.selected_opinion.id if vote else None

        return None


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge

        fields = [
            'id',
            'name',
            'badge_type',
            'tier',
            'description',
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(
        source='badge.name',
        read_only=True
    )

    badge_type = serializers.CharField(
        source='badge.badge_type',
        read_only=True
    )

    badge_description = serializers.CharField(
        source='badge.description',
        read_only=True
    )

    class Meta:
        model = UserBadge

        fields = [
            'id',
            'badge',
            'badge_name',
            'badge_type',
            'badge_description',
            'tier',
            'is_favourite',
            'earned_at',
        ]


class GreenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='target_user.username',
        read_only=True
    )

    profile_picture = serializers.ImageField(
        source='target_user.profile.profile_picture',
        read_only=True
    )

    class Meta:
        model = Green

        fields = [
            'id',
            'target_user',
            'username',
            'profile_picture',
            'created_at',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = UserProfile

        fields = [
            'id',
            'username',
            'bio',
            'profile_picture',
            'is_subscriber',
            'subscription_ends_at',
            'created_at',
        ]


class BattleOptionSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = BattleOption

        fields = [
            'id',
            'text',
            'vote_count',
            'percentage',
            'is_winner',
        ]

    def get_percentage(self, obj):
        total_votes = sum(
            option.vote_count
            for option in obj.battle.options.all()
        )

        if total_votes == 0:
            return 0

        return round(
            (obj.vote_count / total_votes) * 100,
            2
        )


class BattleArenaSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(
        source='creator.username',
        read_only=True
    )

    options = BattleOptionSerializer(
        many=True,
        read_only=True
    )

    total_votes = serializers.SerializerMethodField()

    user_voted = serializers.SerializerMethodField()

    selected_option = serializers.SerializerMethodField()

    class Meta:
        model = BattleArena

        fields = [
            'id',
            'creator',
            'creator_username',
            'battle_type',
            'question',
            'is_urgent',
            'status',
            'options',
            'total_votes',
            'user_voted',
            'selected_option',
            'starts_at',
            'ends_at',
            'glow_ends_at',
            'result_delete_at',
            'created_at',
        ]

    def get_total_votes(self, obj):
        return sum(
            option.vote_count
            for option in obj.options.all()
        )

    def get_user_voted(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return BattleArenaVote.objects.filter(
                battle=obj,
                user=request.user
            ).exists()

        return False

    def get_selected_option(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            vote = BattleArenaVote.objects.filter(
                battle=obj,
                user=request.user
            ).first()

            return vote.option.id if vote else None

        return None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification

        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'is_global',
            'is_read',
            'created_at',
        ]


class PublicProfileSerializer(serializers.ModelSerializer):
    favourite_badges = serializers.SerializerMethodField()

    all_badges = serializers.SerializerMethodField()

    opinions_count = serializers.SerializerMethodField()

    total_likes_received = serializers.SerializerMethodField()

    battles_won = serializers.SerializerMethodField()

    greens_count = serializers.SerializerMethodField()

    greening_count = serializers.SerializerMethodField()

    profile_picture = serializers.ImageField(
        source='profile.profile_picture',
        read_only=True
    )

    bio = serializers.CharField(
        source='profile.bio',
        read_only=True
    )

    class Meta:
        model = User

        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'district',
            'profile_picture',
            'bio',
            'date_joined',
            'favourite_badges',
            'all_badges',
            'opinions_count',
            'total_likes_received',
            'battles_won',
            'greens_count',
            'greening_count',
        ]

    def get_favourite_badges(self, obj):
        badges = UserBadge.objects.filter(
            user=obj,
            is_favourite=True
        )[:3]

        return UserBadgeSerializer(
            badges,
            many=True
        ).data

    def get_all_badges(self, obj):
        badges = UserBadge.objects.filter(
            user=obj
        ).order_by('-earned_at')

        return UserBadgeSerializer(
            badges,
            many=True
        ).data

    def get_opinions_count(self, obj):
        return Opinion.objects.filter(
            user=obj,
            is_deleted=False
        ).count()

    def get_total_likes_received(self, obj):
        opinions = Opinion.objects.filter(
            user=obj,
            is_deleted=False
        )

        return sum(
            opinion.like_count
            for opinion in opinions
        )

    def get_battles_won(self, obj):
        return Battle.objects.filter(
            winner_opinion__user=obj
        ).count()

    def get_greens_count(self, obj):
        return Green.objects.filter(
            target_user=obj
        ).count()

    def get_greening_count(self, obj):
        return Green.objects.filter(
            user=obj
        ).count()