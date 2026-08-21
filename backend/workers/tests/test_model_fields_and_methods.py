from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from workers.models import JobCategory, WorkerProfile, WorkerWorkImage, Booking, Conversation, Message, BookingReview


class WorkerModelFieldsAndMethodsTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='f_cust', email='fcust@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='f_work', email='fwork@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Mason', price=Decimal('65.50'), is_online=True)

    def test_worker_profile_price_decimal_type(self):
        self.assertIsInstance(self.worker_profile.price, Decimal)
        self.assertEqual(self.worker_profile.price, Decimal('65.50'))

    def test_worker_profile_rating_default(self):
        p = WorkerProfile.objects.create(
            user=User.objects.create_user(username='new_w', email='nw@example.com', password='pwd', role='worker'),
            category='Welder',
            price=Decimal('50.00')
        )
        self.assertEqual(p.rating, 4.8)
        self.assertEqual(p.total_reviews, 120)

    def test_worker_work_image_cascade_delete(self):
        img = WorkerWorkImage.objects.create(worker=self.worker_profile, image='sample.jpg', sort_order=0)
        img_id = img.id
        self.worker_profile.delete()
        self.assertFalse(WorkerWorkImage.objects.filter(id=img_id).exists())

    def test_booking_cascade_on_customer_delete(self):
        b = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Mason',
            address='Site Address',
            scheduled_at=timezone.now(),
            total_amount=Decimal('131.00')
        )
        b_id = b.id
        self.customer.delete()
        self.assertFalse(Booking.objects.filter(id=b_id).exists())

    def test_conversation_cascade_on_booking_delete(self):
        b = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Mason',
            address='Site Address',
            scheduled_at=timezone.now(),
            total_amount=Decimal('131.00')
        )
        conv = Conversation.objects.create(booking=b, customer=self.customer, worker=self.worker_profile)
        conv_id = conv.id
        b.delete()
        self.assertFalse(Conversation.objects.filter(id=conv_id).exists())

    def test_message_cascade_on_conversation_delete(self):
        b = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Mason',
            address='Site Address',
            scheduled_at=timezone.now(),
            total_amount=Decimal('131.00')
        )
        conv = Conversation.objects.create(booking=b, customer=self.customer, worker=self.worker_profile)
        msg = Message.objects.create(conversation=conv, sender=self.customer, text='Hello')
        msg_id = msg.id
        conv.delete()
        self.assertFalse(Message.objects.filter(id=msg_id).exists())
