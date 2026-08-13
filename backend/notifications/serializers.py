from rest_framework import serializers
from .models import DeviceToken, Notification, Platform


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Used for registering / updating an FCM device token."""
    platform = serializers.ChoiceField(
        choices=[Platform.ANDROID, Platform.IOS, Platform.WEB],
        default=Platform.ANDROID,
    )

    class Meta:
        model = DeviceToken
        fields = ['token', 'platform']

    def validate_token(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('FCM token cannot be empty.')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only serializer for listing user notifications."""
    related_booking_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'related_booking_id',
            'data',
            'is_read',
            'created_at',
        ]
        read_only_fields = fields

    def get_related_booking_id(self, obj):
        return obj.related_booking_id
