from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver




class User(AbstractUser):
    district = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=255, blank=True, null=True)
    ban_until = models.DateTimeField(blank=True, null=True)

    def currently_banned(self):
        if not self.is_banned:
            return False

        if self.ban_until and timezone.now() > self.ban_until:
            self.is_banned = False
            self.ban_reason = None
            self.ban_until = None
            self.save()
            return False

        return True

    def __str__(self):
        return self.username
    
    
class Follow(models.Model):
    # 🟢 THE FIX: Use settings.AUTH_USER_MODEL instead of User
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='following', 
        on_delete=models.CASCADE
    )
    
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='followers', 
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} greens {self.followed.username}"
    
    
class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} greens {self.followed.username}"

# 🟢 PASTE THIS ENTIRE BLOCK AT THE BOTTOM:
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=600, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    subscription_ends_at = models.DateTimeField(null=True, blank=True)
    is_subscriber = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# These signals automatically create a profile the second a user signs up!
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    
