from django.test import TestCase, RequestFactory
from django.utils import timezone
from rest_framework import serializers
from accounts.models import User
from workers.models import (
    JobCategory,
    WorkerProfile,
    Booking,
    Conversation,
    Message,
    BookingReview,
)
from workers.serializers import (
    JobCategorySerializer,
    WorkerProfileSerializer,
    PublicWorkerProfileSerializer,
    WorkerProfileCreateSerializer,
    BookingSerializer,
    BookingCreateSerializer,
    BookingStatusUpdateSerializer,
    BookingReviewSerializer,
    BookingReviewCreateSerializer,
    ConversationSerializer,
    MessageSerializer,
)


class WorkerSerializerTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='ser_cust', email='sc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='ser_work', email='sw@example.com', password='pwd', role='worker', phone_number='8887776665', location='Tech City')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Electrician', price=50.00, bio='Experienced electrician', is_online=True)

    def test_job_category_serializer(self):
        cat = JobCategory.objects.create(name='Carpentry', sort_order=1)
        serializer = JobCategorySerializer(cat)
        self.assertEqual(serializer.data['name'], 'Carpentry')

    def test_worker_profile_serializer_full_details(self):
        serializer = WorkerProfileSerializer(self.worker_profile)
        data = serializer.data
        self.assertEqual(data['category'], 'Electrician')
        self.assertEqual(data['user']['email'], 'sw@example.com')
        self.assertEqual(data['user']['phone_number'], '8887776665')

    def test_public_worker_profile_serializer_masks_pii(self):
        serializer = PublicWorkerProfileSerializer(self.worker_profile)
        data = serializer.data
        self.assertEqual(data['category'], 'Electrician')
        self.assertNotIn('email', data['user'])
        self.assertNotIn('phone_number', data['user'])

    def test_worker_profile_create_serializer_valid(self):
        data = {
            'category': 'plumber',
            'price': 65.00,
            'experience_years': 4,
            'bio': 'Licensed professional',
            'username': 'plumber_pro',
            'phone_number': '7778889990'
        }
        serializer = WorkerProfileCreateSerializer(instance=self.worker_profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.category, 'Plumber')
        self.assertEqual(float(updated.price), 65.00)
        self.worker_user.refresh_from_db()
        self.assertEqual(self.worker_user.username, 'plumber_pro')

    def test_worker_profile_create_serializer_invalid_price(self):
        serializer = WorkerProfileCreateSerializer(data={'category': 'Plumber', 'price': -10.00})
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_worker_profile_create_serializer_invalid_experience(self):
        serializer = WorkerProfileCreateSerializer(data={'category': 'Plumber', 'price': 50.00, 'experience_years': -1})
        self.assertFalse(serializer.is_valid())
        self.assertIn('experience_years', serializer.errors)


class BookingSerializerTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='book_cust', email='bc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='book_work', email='bw@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Painter', price=40.00, is_online=True)
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = self.customer

    def test_booking_create_serializer_success(self):
        data = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Painter',
            'description': 'Paint 2 bedrooms',
            'address': '789 Pine Road',
            'service_latitude': 17.40,
            'service_longitude': 78.45,
            'scheduled_at': timezone.now() + timezone.timedelta(days=1),
            'total_amount': 200.00
        }
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        booking = serializer.save()
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.worker, self.worker_profile)
        # Check auto created conversation and first message
        self.assertTrue(hasattr(booking, 'conversation'))
        self.assertEqual(booking.conversation.messages.count(), 1)

    def test_booking_create_serializer_offline_worker_rejected(self):
        self.worker_profile.is_online = False
        self.worker_profile.save()

        data = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Painter',
            'address': '789 Pine Road',
            'scheduled_at': timezone.now() + timezone.timedelta(days=1),
            'total_amount': 200.00
        }
        serializer = BookingCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('worker_id', serializer.errors)

    def test_booking_status_transitions(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Painter',
            address='Address',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )

        # Valid transition: requested -> accepted
        s1 = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_ACCEPTED}, context={'booking': booking})
        self.assertTrue(s1.is_valid())

        # Valid transition: requested -> declined
        s2 = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_DECLINED}, context={'booking': booking})
        self.assertTrue(s2.is_valid())

        # Invalid transition: requested -> completed
        s3 = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_COMPLETED}, context={'booking': booking})
        self.assertFalse(s3.is_valid())


class BookingReviewSerializerTests(TestCase):
    def test_review_create_serializer_valid(self):
        serializer = BookingReviewCreateSerializer(data={'rating': 5, 'feedback': 'Great service!'})
        self.assertTrue(serializer.is_valid())

    def test_review_create_serializer_invalid_rating(self):
        s1 = BookingReviewCreateSerializer(data={'rating': 0})
        self.assertFalse(s1.is_valid())

        s2 = BookingReviewCreateSerializer(data={'rating': 6})
        self.assertFalse(s2.is_valid())


class ConversationSerializerTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cust_user', email='cu@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='work_user', email='wu@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Gardener', price=35.00)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Gardener',
            address='Garden address',
            scheduled_at=timezone.now(),
            total_amount=70.00
        )
        self.conversation = Conversation.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile
        )

    def test_conversation_serializer_unread_count_and_party_name(self):
        Message.objects.create(conversation=self.conversation, sender=self.worker_user, text='On my way!', is_read=False)
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.customer

        serializer = ConversationSerializer(self.conversation, context={'request': request})
        data = serializer.data
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(data['other_party_name'], 'work user')
        self.assertIsNotNone(data['last_message'])
