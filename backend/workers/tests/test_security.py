from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from workers.models import Booking, WorkerProfile


class WorkerSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_user = User.objects.create_user(
            username='cust_sec',
            email='cust_sec@example.com',
            password='Password123!',
            role='customer'
        )
        self.worker_user = User.objects.create_user(
            username='work_sec',
            email='work_sec@example.com',
            password='Password123!',
            role='worker',
            phone_number='9998887776',
            location='Secret Worker Base'
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Plumber',
            price=50.00,
            is_online=True
        )

    def test_public_worker_list_masks_user_info(self):
        res = self.client.get('/api/workers/nearby/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        worker_data = res.data['list'][0]
        user_info = worker_data['user']
        self.assertNotIn('email', user_info)
        self.assertNotIn('phone_number', user_info)
        self.assertNotIn('latitude', user_info)
        self.assertNotIn('longitude', user_info)

    def test_customer_booking_cancellation(self):
        booking = Booking.objects.create(
            customer=self.customer_user,
            worker=self.worker_profile,
            service_category='Plumber',
            address='123 Main St',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )

        self.client.force_authenticate(user=self.customer_user)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)

    def test_worker_cannot_cancel_via_customer_endpoint(self):
        booking = Booking.objects.create(
            customer=self.customer_user,
            worker=self.worker_profile,
            service_category='Plumber',
            address='123 Main St',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )

        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
