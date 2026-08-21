from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from workers.models import (
    JobCategory,
    WorkerProfile,
    Booking,
    Conversation,
    Message,
    BookingReview,
)
from accounts.tests.test_serializers import create_dummy_image


class WorkerViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='view_cust',
            email='vc@example.com',
            password='Password123!',
            role='customer'
        )
        self.worker_user = User.objects.create_user(
            username='view_work',
            email='vw@example.com',
            password='Password123!',
            role='worker',
            phone_number='9988776655',
            location='Gachibowli',
            latitude=17.440081,
            longitude=78.348915
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Electrician',
            price=60.00,
            bio='Expert electrician',
            is_online=True
        )

    def test_worker_profile_detail_get_authenticated(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.get('/api/workers/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['category'], 'Electrician')

    def test_worker_profile_create_customer_forbidden(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.post('/api/workers/profile/', {'category': 'Plumber', 'price': 50.00})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_worker_availability_toggle(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch('/api/workers/availability/', {'is_online': False})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.worker_profile.refresh_from_db()
        self.assertFalse(self.worker_profile.is_online)

    def test_worker_dashboard_summary(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.get('/api/workers/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', res.data)
        self.assertIn('pending_requests', res.data['metrics'])
        self.assertIn('active_jobs', res.data['metrics'])
        self.assertIn('completed_jobs', res.data['metrics'])

    def test_worker_booking_list(self):
        Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.get('/api/workers/bookings/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)

    def test_worker_booking_status_update(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_ACCEPTED})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_ACCEPTED)

    def test_customer_booking_create(self):
        self.client.force_authenticate(user=self.customer)
        payload = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Electrician',
            'description': 'Install ceiling fan',
            'address': 'Flat 101, Sky Towers',
            'service_latitude': 17.44,
            'service_longitude': 78.34,
            'scheduled_at': (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            'total_amount': '120.00'
        }
        res = self.client.post('/api/workers/bookings/create/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['service_category'], 'Electrician')

    def test_customer_booking_list(self):
        Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/workers/bookings/my/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)

    def test_customer_booking_cancel(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)

    def test_booking_review_create_and_recalculate_rating(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_COMPLETED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{booking.id}/review/', {'rating': 5, 'feedback': 'Outstanding!'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_profile.rating, 5.0)
        self.assertEqual(self.worker_profile.total_reviews, 1)

    def test_conversation_list_and_messages(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00
        )
        conv = Conversation.objects.create(booking=booking, customer=self.customer, worker=self.worker_profile)
        Message.objects.create(conversation=conv, sender=self.customer, text='Hello worker!', is_read=False)

        # Customer reads messages
        self.client.force_authenticate(user=self.customer)
        res = self.client.get(f'/api/workers/conversations/{conv.id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)

        # Worker sends reply
        self.client.force_authenticate(user=self.worker_user)
        post_res = self.client.post(f'/api/workers/conversations/{conv.id}/messages/', {'text': 'Hello customer!'})
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)

    def test_categories_and_job_category_options(self):
        JobCategory.objects.get_or_create(name='Painter', defaults={'sort_order': 1})
        res1 = self.client.get('/api/workers/categories/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        res2 = self.client.get('/api/workers/job-categories/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

    def test_nearby_workers_and_public_detail(self):
        # Nearby search
        res1 = self.client.get('/api/workers/nearby/?category=Electrician&lat=17.44&lng=78.34')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res1.data['list']) >= 1)

        # Public detail
        res2 = self.client.get(f'/api/workers/{self.worker_profile.id}/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['category'], 'Electrician')

    def test_worker_work_image_upload_and_delete(self):
        self.client.force_authenticate(user=self.worker_user)
        dummy_img = create_dummy_image('JPEG')
        upload_res = self.client.post(
            '/api/workers/profile/work-images/',
            {'images': [dummy_img], 'caption': 'My work sample'},
            format='multipart'
        )
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        image_id = upload_res.data['list'][0]['id']

        # Delete image
        del_res = self.client.delete(f'/api/workers/profile/work-images/{image_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
