from django.contrib import admin
from .models import DeviceToken, Notification


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'is_active', 'token_preview', 'updated_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__username', 'user__email', 'token']
    ordering = ['-updated_at']

    @admin.display(description='Token (preview)')
    def token_preview(self, obj):
        return f'{obj.token[:32]}…' if len(obj.token) > 32 else obj.token


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['recipient__username', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'data']
