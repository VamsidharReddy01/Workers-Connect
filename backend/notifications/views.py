from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import DeviceToken, Notification
from .serializers import DeviceTokenSerializer, NotificationSerializer


class DeviceTokenView(APIView):
    """
    POST /api/notifications/device-token/

    Register or update an FCM device token for the authenticated user.
    If the token already exists (any user), it is claimed by the current user
    and set to active. This handles token refresh correctly without duplicates.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = (request.data.get('token') or '').strip()
        platform = (request.data.get('platform') or 'android').strip()

        if not token:
            return Response({'errors': {'token': ['FCM token cannot be empty.']}}, status=status.HTTP_400_BAD_REQUEST)
        if platform not in ('android', 'ios', 'web'):
            platform = 'android'

        # Upsert: update if token exists, otherwise create.
        # We do this at the DB level directly to avoid serializer uniqueness issues.
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'platform': platform,
                'is_active': True,
            },
        )
        return Response(
            {'message': 'Device token registered.', 'created': created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        """
        DELETE /api/notifications/device-token/
        Deactivate a specific token (called on logout).
        Accepts { "token": "..." } in the request body.
        """
        token = (request.data.get('token') or '').strip()
        if token:
            DeviceToken.objects.filter(user=request.user, token=token).update(is_active=False)
        else:
            # Deactivate ALL tokens for this user (full logout)
            DeviceToken.objects.filter(user=request.user).update(is_active=False)
        return Response({'message': 'Device token(s) deactivated.'}, status=status.HTTP_200_OK)


class NotificationListView(APIView):
    """
    GET /api/notifications/
    Returns all notifications for the current user, most recent first.
    Optional query param: ?unread_only=true
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(recipient=request.user).select_related(
            'related_booking'
        )
        if request.query_params.get('unread_only', '').lower() in ('1', 'true', 'yes'):
            queryset = queryset.filter(is_read=False)
        serializer = NotificationSerializer(queryset[:100], many=True)
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)


class UnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Returns { "count": N } for the current user's unread notifications.
    Lightweight — used to drive the notification badge.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'count': count}, status=status.HTTP_200_OK)


class MarkNotificationReadView(APIView):
    """
    PATCH /api/notifications/<id>/read/
    Mark a single notification as read.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    def post(self, request, notification_id):
        return self.patch(request, notification_id)



class MarkAllReadView(APIView):
    """
    POST /api/notifications/mark-all-read/
    Mark every unread notification as read for the current user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'marked_read': updated}, status=status.HTTP_200_OK)
