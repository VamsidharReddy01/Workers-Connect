from django.db import models
from django.conf import settings


class NotificationType:
    """Structured constants for notification types."""
    JOB_REQUEST_RECEIVED = 'JOB_REQUEST_RECEIVED'
    JOB_ACCEPTED = 'JOB_ACCEPTED'
    JOB_DECLINED = 'JOB_DECLINED'
    WORKER_ON_THE_WAY = 'WORKER_ON_THE_WAY'
    JOB_STARTED = 'JOB_STARTED'
    JOB_COMPLETED = 'JOB_COMPLETED'
    JOB_CANCELLED = 'JOB_CANCELLED'
    NEW_MESSAGE = 'NEW_MESSAGE'
    SYSTEM_NOTIFICATION = 'SYSTEM_NOTIFICATION'

    CHOICES = [
        (JOB_REQUEST_RECEIVED, 'Job Request Received'),
        (JOB_ACCEPTED, 'Job Accepted'),
        (JOB_DECLINED, 'Job Declined'),
        (WORKER_ON_THE_WAY, 'Worker On The Way'),
        (JOB_STARTED, 'Job Started'),
        (JOB_COMPLETED, 'Job Completed'),
        (JOB_CANCELLED, 'Job Cancelled'),
        (NEW_MESSAGE, 'New Message'),
        (SYSTEM_NOTIFICATION, 'System Notification'),
    ]


class Platform:
    ANDROID = 'android'
    IOS = 'ios'
    WEB = 'web'

    CHOICES = [
        (ANDROID, 'Android'),
        (IOS, 'iOS'),
        (WEB, 'Web'),
    ]


class DeviceToken(models.Model):
    """
    Stores FCM push notification tokens for authenticated user devices.
    A single user may have multiple active devices.
    Tokens are unique — updating a token upserts the existing record.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
    )
    token = models.CharField(max_length=512, unique=True, db_index=True)
    platform = models.CharField(
        max_length=10,
        choices=Platform.CHOICES,
        default=Platform.ANDROID,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.username} — {self.platform} ({self.token[:24]}…)'


class Notification(models.Model):
    """
    Persisted in-app notification record.
    Created whenever a push notification is sent so users can view
    their notification history even if the push was missed.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.CHOICES,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    # Nullable FK so the notification record survives if the booking is deleted
    related_booking = models.ForeignKey(
        'workers.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    # Extra arbitrary data payload (e.g. conversation_id for chat notifications)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
        ]

    def __str__(self):
        return f'[{self.notification_type}] → {self.recipient.username}'
