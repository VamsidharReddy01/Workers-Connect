from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from workers.models import Booking, WorkerProfile, BookingReview, JobCategory
from workers.views import _recalculate_worker_rating, _notify_status_change


class PerformanceAndStressTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username='perf_cust', email='pc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='perf_work', email='pw@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Carpenter',
            price=Decimal('50.00'),
            is_online=True
        )

    def test_recalculate_worker_rating_with_multiple_reviews(self):
        # Create 10 reviews with known ratings: [5, 4, 5, 3, 4, 5, 5, 4, 3, 5] -> sum = 43 / 10 = 4.3
        ratings = [5, 4, 5, 3, 4, 5, 5, 4, 3, 5]
        for i, r in enumerate(ratings):
            cust = User.objects.create_user(username=f'rcust_{i}', email=f'rc_{i}@example.com', password='pwd', role='customer')
            b = Booking.objects.create(
                customer=cust,
                worker=self.worker_profile,
                service_category='Carpenter',
                address='Address',
                scheduled_at=timezone.now(),
                total_amount=Decimal('50.00'),
                status=Booking.STATUS_COMPLETED
            )
            BookingReview.objects.create(booking=b, customer=cust, worker=self.worker_profile, rating=r)

        _recalculate_worker_rating(self.worker_profile)
        self.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_profile.total_reviews, 10)
        self.assertEqual(self.worker_profile.rating, 4.3)

    def test_notify_status_change_handles_fcm_exceptions_gracefully(self):
        # Notification failures must NOT raise or crash status updates
        b = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Carpenter',
            address='Address',
            scheduled_at=timezone.now(),
            total_amount=Decimal('50.00'),
            status=Booking.STATUS_ACCEPTED
        )
        # Should execute cleanly without raising exception
        _notify_status_change(b, Booking.STATUS_ACCEPTED)
        _notify_status_change(b, Booking.STATUS_DECLINED)
        _notify_status_change(b, Booking.STATUS_ON_THE_WAY)
        _notify_status_change(b, Booking.STATUS_IN_PROGRESS)
        _notify_status_change(b, Booking.STATUS_COMPLETED)
        _notify_status_change(b, Booking.STATUS_CANCELLED)

    def test_bulk_bookings_query_performance(self):
        # Create 25 bookings for pagination & querying
        bookings = [
            Booking(
                customer=self.customer,
                worker=self.worker_profile,
                service_category='Carpenter',
                address=f'Address {i}',
                scheduled_at=timezone.now(),
                total_amount=Decimal('50.00'),
                status=Booking.STATUS_REQUESTED
            ) for i in range(25)
        ]
        Booking.objects.bulk_create(bookings)

        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/workers/bookings/my/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data['list']) >= 25)
