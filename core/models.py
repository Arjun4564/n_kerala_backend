from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

class Topic(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class Opinion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='opinions'
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='opinions'
    )

    content = models.TextField(max_length=120)

    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    boost_count = models.PositiveIntegerField(default=0)

    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)

    trending_score = models.FloatField(default=0)

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_hidden = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['topic']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.content[:40]}"


class OpinionLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        related_name='likes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'opinion')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            Opinion.objects.filter(id=self.opinion.id).update(
                like_count=F('like_count') + 1
            )

    def delete(self, *args, **kwargs):
        Opinion.objects.filter(id=self.opinion.id).update(
            like_count=F('like_count') - 1
        )

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} liked {self.opinion.id}"


class OpinionBoost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        related_name='boosts'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'opinion')

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            Opinion.objects.filter(id=self.opinion.id).update(
                boost_count=F('boost_count') + 1
            )

    def delete(self, *args, **kwargs):
        Opinion.objects.filter(id=self.opinion.id).update(
            boost_count=F('boost_count') - 1
        )

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} boosted {self.opinion.id}"


class OpinionReply(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    content = models.TextField(max_length=150)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            Opinion.objects.filter(id=self.opinion.id).update(
                reply_count=F('reply_count') + 1
            )

    def delete(self, *args, **kwargs):
        Opinion.objects.filter(id=self.opinion.id).update(
            reply_count=F('reply_count') - 1
        )

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.content[:40]}"


class Report(models.Model):
    REPORT_TYPES = [
        ('user', 'User'),
        ('opinion', 'Opinion'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )

    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_received'
    )

    opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    reason = models.TextField()

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reporter.username} reported {self.reported_user.username}"


class AvasthaMood(models.Model):
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('normal', 'Normal'),
        ('sad', 'Sad'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES
    )

    date = models.DateField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.mood}"


class Battle(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    title = models.CharField(max_length=150)

    opinion_a = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        related_name='battle_opinion_a'
    )

    opinion_b = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        related_name='battle_opinion_b'
    )

    vote_a_count = models.PositiveIntegerField(default=0)
    vote_b_count = models.PositiveIntegerField(default=0)

    winner_opinion = models.ForeignKey(
        Opinion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_battles'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.opinion_a == self.opinion_b:
            raise ValidationError(
                "Battle opinions must be different."
            )

    def __str__(self):
        return self.title


class BattleVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    battle = models.ForeignKey(
        Battle,
        on_delete=models.CASCADE,
        related_name='votes'
    )

    selected_opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'battle')

    def clean(self):
        if self.selected_opinion not in [
            self.battle.opinion_a,
            self.battle.opinion_b
        ]:
            raise ValidationError(
                "Invalid opinion selected."
            )

    def __str__(self):
        return f"{self.user.username} voted in {self.battle.title}"


class Badge(models.Model):
    BADGE_TYPES = [
        ('achievement', 'Achievement'),
        ('special', 'Special'),
        ('subscriber', 'Subscriber'),
    ]

    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('diamond', 'Diamond'),
    ]

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    badge_type = models.CharField(
        max_length=30,
        choices=BADGE_TYPES,
        default='achievement'
    )

    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='bronze'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE
    )

    tier = models.CharField(max_length=20)

    is_favourite = models.BooleanField(default=False)

    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"




class BattleArena(models.Model):
    BATTLE_TYPES = [
        ("one_vs_one", "1 vs 1"),
        ("four_option", "4 Option"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("glow", "Winner Glow"),
        ("result", "Result"),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_battles"
    )

    battle_type = models.CharField(
        max_length=20,
        choices=BATTLE_TYPES
    )

    question = models.CharField(max_length=150)

    is_urgent = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    starts_at = models.DateTimeField(auto_now_add=True)

    ends_at = models.DateTimeField()

    glow_ends_at = models.DateTimeField(
        null=True,
        blank=True
    )

    result_delete_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ends_at']),
        ]

    def __str__(self):
        return self.question


class BattleOption(models.Model):
    battle = models.ForeignKey(
        BattleArena,
        on_delete=models.CASCADE,
        related_name="options"
    )

    text = models.CharField(max_length=60)

    vote_count = models.PositiveIntegerField(default=0)

    is_winner = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class BattleArenaVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    battle = models.ForeignKey(
        BattleArena,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    option = models.ForeignKey(
        BattleOption,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "battle")


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
         ('admin', 'Admin'),
        ('updates', 'Updates'),
        ('promos', 'Promos'),
        
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    opinion = models.ForeignKey(
        Opinion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=120)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='admin'
    )

    is_global = models.BooleanField(default=False)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title
    
    
    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile whenever a new User signs up."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Automatically save the profile when the User is saved."""
    instance.profile.save()
    
    
@receiver(post_save, sender=Notification)
def broadcast_global_notification(sender, instance, created, **kwargs):
    # 🟢 Intercept the save! If it's brand new and marked as global...
    if created and instance.is_global:
        
        # 1. Grab every single user in your app
        all_users = User.objects.all()
        
        # 2. Build a personalized copy for each user
        bulk_notifs = []
        for user in all_users:
            bulk_notifs.append(
                Notification(
                    user=user,  # Assigns it specifically to this user
                    title=instance.title,
                    message=instance.message,
                    notification_type=instance.notification_type,
                    is_global=False, # Turn off the global flag for the copies
                    is_read=False,
                    is_deleted=False
                )
            )
            
        # 3. Fire them all into the database instantly
        Notification.objects.bulk_create(bulk_notifs)
        
        # 4. Delete the original "template" you just made in the admin panel
        # so it doesn't cause duplicates!
        instance.delete()