from django.urls import path
from .views import (
    DeviceTokenView,
    MarkAllReadView,
    MarkNotificationReadView,
    NotificationListView,
    UnreadCountView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', UnreadCountView.as_view(), name='notification-unread-count'),
    path('device-token/', DeviceTokenView.as_view(), name='notification-device-token'),
    path('<int:notification_id>/read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', MarkAllReadView.as_view(), name='notification-mark-all-read'),
]
