from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from workers.models import Booking, WorkerProfile, Conversation, Message
from notifications.models import Notification, NotificationType, DeviceToken
from notifications.services import NotificationService


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='srv_cust', email='scust@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='srv_work', email='swork@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Plumber', price=40.00)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='123 Service Road',
            scheduled_at=timezone.now(),
            total_amount=80.00
        )
        self.conversation = Conversation.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile
        )

    def test_send_persists_notification_in_db(self):
        notif = NotificationService.send(
            recipient=self.customer,
            notification_type=NotificationType.SYSTEM_NOTIFICATION,
            title='System Alert',
            message='Your account security check is complete.',
            booking=self.booking
        )
        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.recipient, self.customer)
        self.assertEqual(Notification.objects.filter(recipient=self.customer).count(), 1)

    def test_notify_new_job_request(self):
        NotificationService.notify_new_job_request(self.booking)
        notif = Notification.objects.filter(recipient=self.worker_user).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_REQUEST_RECEIVED)

    def test_notify_job_accepted(self):
        NotificationService.notify_job_accepted(self.booking)
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_ACCEPTED)

    def test_notify_job_declined(self):
        NotificationService.notify_job_declined(self.booking)
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_DECLINED)

    def test_notify_worker_on_the_way(self):
        NotificationService.notify_worker_on_the_way(self.booking)
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.WORKER_ON_THE_WAY)

    def test_notify_job_started(self):
        NotificationService.notify_job_started(self.booking)
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_STARTED)

    def test_notify_job_completed(self):
        NotificationService.notify_job_completed(self.booking)
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_COMPLETED)

    def test_notify_job_cancelled_by_customer(self):
        NotificationService.notify_job_cancelled(self.booking, cancelled_by='customer')
        notif = Notification.objects.filter(recipient=self.worker_user).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_CANCELLED)

    def test_notify_job_cancelled_by_worker(self):
        NotificationService.notify_job_cancelled(self.booking, cancelled_by='worker')
        notif = Notification.objects.filter(recipient=self.customer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.JOB_CANCELLED)

    def test_notify_new_message(self):
        msg = Message.objects.create(conversation=self.conversation, sender=self.customer, text='Hello worker!')
        NotificationService.notify_new_message(msg, self.conversation)
        notif = Notification.objects.filter(recipient=self.worker_user).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, NotificationType.NEW_MESSAGE)
