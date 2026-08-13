"""
Centralized notification service for WorkersBridge.

Responsibilities:
  1. Persist a Notification record in the database.
  2. Find active FCM device tokens for the recipient.
  3. Build the FCM payload (never includes sensitive data).
  4. Send the push notification via Firebase Admin SDK.
  5. Remove invalid / expired tokens automatically.
  6. Log all failures — FCM errors NEVER block business logic callers.

Usage (from views / serializers):
    from notifications.services import NotificationService

    NotificationService.notify_job_accepted(booking=booking)
"""

import logging
import os

from django.conf import settings

from .models import DeviceToken, Notification, NotificationType

logger = logging.getLogger(__name__)

# ── Firebase Admin SDK initialisation ────────────────────────────────────────
# Lazy-initialised so the app starts even without Firebase credentials
# (useful for running tests or the dev server without FCM configured).
_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app

        cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', None) or os.getenv(
            'FIREBASE_SERVICE_ACCOUNT_PATH'
        )
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # Fall back to Application Default Credentials (useful on GCP / Cloud Run)
            _firebase_app = firebase_admin.initialize_app()

        return _firebase_app
    except ImportError:
        logger.warning(
            'firebase-admin package not installed. Push notifications are disabled. '
            'Run: pip install firebase-admin'
        )
        return None
    except Exception as exc:
        logger.error('Firebase Admin SDK initialisation failed: %s', exc)
        return None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _send_fcm_to_tokens(tokens: list[str], title: str, body: str, data: dict) -> None:
    """
    Sends an FCM multicast message to the given token list.
    Removes tokens that FCM reports as invalid or unregistered.
    All errors are caught and logged — callers are never interrupted.
    """
    if not tokens:
        return

    firebase_app = _get_firebase_app()
    if firebase_app is None:
        logger.info(
            'FCM skipped (no Firebase app). Would send "%s" to %d device(s).', title, len(tokens)
        )
        return

    try:
        from firebase_admin import messaging

        # Stringify all data values — FCM requires string key/value pairs
        str_data = {k: str(v) for k, v in (data or {}).items()}

        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body),
            data=str_data,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='job_updates',
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                ),
            ),
        )
        response = messaging.send_each_for_multicast(message, app=firebase_app)
        logger.info(
            'FCM multicast: %d success, %d failure for title="%s"',
            response.success_count,
            response.failure_count,
            title,
        )

        # Remove tokens that are no longer registered
        invalid_tokens = []
        for idx, result in enumerate(response.responses):
            if not result.success and result.exception:
                error_code = getattr(result.exception, 'code', '')
                if error_code in (
                    'registration-token-not-registered',
                    'invalid-registration-token',
                    'messaging/registration-token-not-registered',
                    'messaging/invalid-registration-token',
                ):
                    invalid_tokens.append(tokens[idx])
        if invalid_tokens:
            removed = DeviceToken.objects.filter(token__in=invalid_tokens).update(is_active=False)
            logger.info('Deactivated %d invalid FCM token(s).', removed)

    except Exception as exc:
        logger.error('FCM send error for title="%s": %s', title, exc)


# ── Public NotificationService ────────────────────────────────────────────────

class NotificationService:
    """
    High-level notification service.  All public methods are class methods
    so callers don't need to instantiate anything.
    """

    @classmethod
    def send(
        cls,
        *,
        recipient,
        notification_type: str,
        title: str,
        message: str,
        booking=None,
        extra_data: dict | None = None,
    ) -> 'Notification':
        """
        Persist a Notification record and attempt FCM push delivery.

        The database write always succeeds.
        FCM failure is logged but does NOT raise an exception.
        """
        data = {}
        if booking is not None:
            data['booking_id'] = str(booking.id)
        if extra_data:
            data.update(extra_data)
        data['notification_type'] = notification_type

        # 1. Persist notification
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            related_booking=booking,
            data=data,
        )

        # 2. Collect active device tokens for this recipient
        tokens = list(
            DeviceToken.objects.filter(user=recipient, is_active=True)
            .values_list('token', flat=True)
        )

        # 3. Push via FCM (errors are caught internally — never block callers)
        try:
            _send_fcm_to_tokens(tokens, title, message, data)
        except Exception as exc:
            logger.error('FCM send raised unexpectedly: %s', exc)

        return notification

    # ── Job lifecycle helpers ─────────────────────────────────────────────────

    @classmethod
    def notify_new_job_request(cls, booking) -> None:
        """Worker receives: new booking request from a customer."""
        worker_user = booking.worker.user
        customer_name = booking.customer.username
        cls.send(
            recipient=worker_user,
            notification_type=NotificationType.JOB_REQUEST_RECEIVED,
            title='New Job Request',
            message=f'{customer_name} requested {booking.service_category} service. Tap to view.',
            booking=booking,
        )

    @classmethod
    def notify_job_accepted(cls, booking) -> None:
        """Customer receives: worker accepted the booking."""
        cls.send(
            recipient=booking.customer,
            notification_type=NotificationType.JOB_ACCEPTED,
            title='Worker Accepted Your Request',
            message=f'Your {booking.service_category} request has been accepted.',
            booking=booking,
        )

    @classmethod
    def notify_job_declined(cls, booking) -> None:
        """Customer receives: worker declined the booking."""
        cls.send(
            recipient=booking.customer,
            notification_type=NotificationType.JOB_DECLINED,
            title='Request Declined',
            message='Your worker could not accept this request.',
            booking=booking,
        )

    @classmethod
    def notify_worker_on_the_way(cls, booking) -> None:
        """Customer receives: worker is on the way."""
        cls.send(
            recipient=booking.customer,
            notification_type=NotificationType.WORKER_ON_THE_WAY,
            title='Worker Is On The Way',
            message='Your worker is on the way to your location.',
            booking=booking,
        )

    @classmethod
    def notify_job_started(cls, booking) -> None:
        """Customer receives: worker started working."""
        cls.send(
            recipient=booking.customer,
            notification_type=NotificationType.JOB_STARTED,
            title='Job Started',
            message='Your worker has started working on your request.',
            booking=booking,
        )

    @classmethod
    def notify_job_completed(cls, booking) -> None:
        """Customer receives: job has been completed."""
        cls.send(
            recipient=booking.customer,
            notification_type=NotificationType.JOB_COMPLETED,
            title='Job Completed',
            message=f'Your {booking.service_category} service has been completed.',
            booking=booking,
        )

    @classmethod
    def notify_job_cancelled(cls, booking, cancelled_by) -> None:
        """The other party receives a cancellation notice."""
        if cancelled_by == 'customer':
            recipient = booking.worker.user
            actor = booking.customer.username
        else:
            recipient = booking.customer
            actor = booking.worker.user.username

        cls.send(
            recipient=recipient,
            notification_type=NotificationType.JOB_CANCELLED,
            title='Job Cancelled',
            message=f'The {booking.service_category} job has been cancelled by {actor}.',
            booking=booking,
        )

    @classmethod
    def notify_new_message(cls, message, conversation) -> None:
        """The other party in a conversation receives a new message notification."""
        sender = message.sender
        # Determine recipient (the other party)
        if sender.id == conversation.customer_id:
            recipient = conversation.worker.user
        else:
            recipient = conversation.customer

        cls.send(
            recipient=recipient,
            notification_type=NotificationType.NEW_MESSAGE,
            title=sender.username,
            message=message.text[:120] if len(message.text) > 120 else message.text,
            booking=conversation.booking,
            extra_data={'conversation_id': str(conversation.id)},
        )
