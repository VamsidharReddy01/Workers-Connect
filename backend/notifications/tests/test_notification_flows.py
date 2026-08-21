from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from workers.models import Booking, WorkerProfile, Conversation, Message
from notifications.models import Notification, NotificationType, DeviceToken
from notifications.services import NotificationService


class NotificationFlowsTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='flow_cust', email='fc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='flow_work', email='fw@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='AC Repair', price=75.00)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='AC Repair',
            address='Main Street 100',
            scheduled_at=timezone.now(),
            total_amount=150.00
        )
        self.conversation = Conversation.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile
        )

    def test_complete_booking_notification_lifecycle(self):
        # Step 1: Customer creates booking -> Worker notified
        NotificationService.notify_new_job_request(self.booking)
        n1 = Notification.objects.filter(recipient=self.worker_user, notification_type=NotificationType.JOB_REQUEST_RECEIVED).first()
        self.assertIsNotNone(n1)
        self.assertEqual(n1.related_booking, self.booking)

        # Step 2: Worker accepts -> Customer notified
        NotificationService.notify_job_accepted(self.booking)
        n2 = Notification.objects.filter(recipient=self.customer, notification_type=NotificationType.JOB_ACCEPTED).first()
        self.assertIsNotNone(n2)

        # Step 3: Worker on the way -> Customer notified
        NotificationService.notify_worker_on_the_way(self.booking)
        n3 = Notification.objects.filter(recipient=self.customer, notification_type=NotificationType.WORKER_ON_THE_WAY).first()
        self.assertIsNotNone(n3)

        # Step 4: Worker starts job -> Customer notified
        NotificationService.notify_job_started(self.booking)
        n4 = Notification.objects.filter(recipient=self.customer, notification_type=NotificationType.JOB_STARTED).first()
        self.assertIsNotNone(n4)

        # Step 5: Worker completes job -> Customer notified
        NotificationService.notify_job_completed(self.booking)
        n5 = Notification.objects.filter(recipient=self.customer, notification_type=NotificationType.JOB_COMPLETED).first()
        self.assertIsNotNone(n5)

    def test_message_preview_truncation_in_notification(self):
        long_text = 'A' * 200
        msg = Message.objects.create(conversation=self.conversation, sender=self.customer, text=long_text)
        NotificationService.notify_new_message(msg, self.conversation)
        notif = Notification.objects.filter(recipient=self.worker_user, notification_type=NotificationType.NEW_MESSAGE).first()
        self.assertIsNotNone(notif)
        # Message preview should be truncated with ellipsis
        self.assertTrue(len(notif.message) <= 130)
        self.assertTrue(notif.message.endswith('…') or notif.message.endswith('...'))

    def test_notification_with_active_and_inactive_device_tokens(self):
        DeviceToken.objects.create(user=self.customer, token='active_tok_1', is_active=True)
        DeviceToken.objects.create(user=self.customer, token='inactive_tok_2', is_active=False)

        # Sending should succeed and persist DB record
        notif = NotificationService.send(
            recipient=self.customer,
            notification_type=NotificationType.SYSTEM_NOTIFICATION,
            title='Alert',
            message='Testing token selection.'
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.recipient, self.customer)
