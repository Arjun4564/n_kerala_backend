from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'district',
        'is_banned',
        'ban_until',
        'is_staff',
        'date_joined',
    )

    list_filter = (
        'is_banned',
        'is_staff',
        'district',
        'date_joined',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    fieldsets = (
        ('Login Info', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'district', 'profile_image')
        }),
        ('Ban Control', {
            'fields': ('is_banned', 'ban_reason', 'ban_until')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )