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
    WorkerWorkImage,
)
from accounts.tests.test_serializers import create_dummy_image


class WorkerViewsEdgeCasesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='w_edge_cust',
            email='wec@example.com',
            password='Password123!',
            role='customer'
        )
        self.other_customer = User.objects.create_user(
            username='w_other_cust',
            email='woc@example.com',
            password='Password123!',
            role='customer'
        )
        self.worker_user = User.objects.create_user(
            username='w_edge_work',
            email='wew@example.com',
            password='Password123!',
            role='worker',
            phone_number='9112233445',
            location='Hitech City',
            latitude=17.4435,
            longitude=78.3772
        )
        self.other_worker_user = User.objects.create_user(
            username='w_other_work',
            email='wow@example.com',
            password='Password123!',
            role='worker',
            phone_number='9223344556',
            location='Kondapur',
            latitude=17.4600,
            longitude=78.3600
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Plumber',
            price=45.00,
            bio='Plumbing pro',
            is_online=True
        )
        self.other_worker_profile = WorkerProfile.objects.create(
            user=self.other_worker_user,
            category='Carpenter',
            price=55.00,
            is_online=True
        )

    # ── Worker Profile Detail View Edge Cases ─────────────────────────────────
    def test_worker_profile_get_uncreated_profile(self):
        new_worker = User.objects.create_user(username='noprofile', email='np@example.com', password='pwd', role='worker')
        self.client.force_authenticate(user=new_worker)
        res = self.client.get('/api/workers/profile/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_worker_profile_patch_partial_fields(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch('/api/workers/profile/', {'price': '70.00', 'bio': 'Updated Bio'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.worker_profile.refresh_from_db()
        self.assertEqual(float(self.worker_profile.price), 70.00)
        self.assertEqual(self.worker_profile.bio, 'Updated Bio')

    def test_worker_profile_patch_negative_price_rejected(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch('/api/workers/profile/', {'price': -5.00})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', res.data['errors'])

    # ── Availability Toggle Edge Cases ────────────────────────────────────────
    def test_availability_toggle_with_string_booleans(self):
        self.client.force_authenticate(user=self.worker_user)
        # 'false' string
        res1 = self.client.patch('/api/workers/availability/', {'is_online': 'false'})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.worker_profile.refresh_from_db()
        self.assertFalse(self.worker_profile.is_online)

        # 'true' string
        res2 = self.client.patch('/api/workers/availability/', {'is_online': 'true'})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.worker_profile.refresh_from_db()
        self.assertTrue(self.worker_profile.is_online)

    def test_availability_toggle_invalid_value(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.patch('/api/workers/availability/', {'is_online': 'invalid_string'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Customer Booking Create Edge Cases ────────────────────────────────────
    def test_booking_create_negative_total_amount(self):
        self.client.force_authenticate(user=self.customer)
        payload = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Plumber',
            'address': 'Test St',
            'scheduled_at': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'total_amount': '-50.00'
        }
        res = self.client.post('/api/workers/bookings/create/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_create_zero_total_amount(self):
        self.client.force_authenticate(user=self.customer)
        payload = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Plumber',
            'address': 'Test St',
            'scheduled_at': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'total_amount': '0.00'
        }
        res = self.client.post('/api/workers/bookings/create/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_create_nonexistent_worker(self):
        self.client.force_authenticate(user=self.customer)
        payload = {
            'worker_id': 999999,
            'service_category': 'Plumber',
            'address': 'Test St',
            'scheduled_at': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'total_amount': '50.00'
        }
        res = self.client.post('/api/workers/bookings/create/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_worker_cannot_create_booking(self):
        self.client.force_authenticate(user=self.worker_user)
        payload = {
            'worker_id': self.other_worker_profile.id,
            'service_category': 'Carpenter',
            'address': 'Test St',
            'scheduled_at': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'total_amount': '55.00'
        }
        res = self.client.post('/api/workers/bookings/create/', payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Booking Status & Transitions Edge Cases ───────────────────────────────
    def test_worker_cannot_access_other_worker_booking(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.other_worker_user)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_ACCEPTED})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_full_lifecycle_transitions(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.worker_user)

        # requested -> accepted
        r1 = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_ACCEPTED})
        self.assertEqual(r1.status_code, status.HTTP_200_OK)

        # accepted -> on_the_way
        r2 = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_ON_THE_WAY})
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        # on_the_way -> in_progress
        r3 = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_IN_PROGRESS})
        self.assertEqual(r3.status_code, status.HTTP_200_OK)

        # in_progress -> completed
        r4 = self.client.patch(f'/api/workers/bookings/{booking.id}/status/', {'status': Booking.STATUS_COMPLETED})
        self.assertEqual(r4.status_code, status.HTTP_200_OK)

    def test_customer_cannot_cancel_completed_booking(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_COMPLETED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_cancel_other_customer_booking(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.other_customer)
        res = self.client.patch(f'/api/workers/bookings/{booking.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ── Booking Review Edge Cases ─────────────────────────────────────────────
    def test_review_non_completed_booking_rejected(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_REQUESTED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{booking.id}/review/', {'rating': 5})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_review_rejected(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Customer Place',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_COMPLETED
        )
        BookingReview.objects.create(booking=booking, customer=self.customer, worker=self.worker_profile, rating=4)

        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{booking.id}/review/', {'rating': 5})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Conversation and Message Edge Cases ───────────────────────────────────
    def test_unauthorized_user_cannot_read_messages(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Place',
            scheduled_at=timezone.now(),
            total_amount=50.00
        )
        conv = Conversation.objects.create(booking=booking, customer=self.customer, worker=self.worker_profile)

        self.client.force_authenticate(user=self.other_customer)
        res = self.client.get(f'/api/workers/conversations/{conv.id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_user_cannot_post_messages(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Place',
            scheduled_at=timezone.now(),
            total_amount=50.00
        )
        conv = Conversation.objects.create(booking=booking, customer=self.customer, worker=self.worker_profile)

        self.client.force_authenticate(user=self.other_customer)
        res = self.client.post(f'/api/workers/conversations/{conv.id}/messages/', {'text': 'Intruder message'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_empty_message_rejected(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Place',
            scheduled_at=timezone.now(),
            total_amount=50.00
        )
        conv = Conversation.objects.create(booking=booking, customer=self.customer, worker=self.worker_profile)

        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/conversations/{conv.id}/messages/', {'text': '   '})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Work Images Edge Cases ────────────────────────────────────────────────
    def test_delete_other_workers_image_forbidden(self):
        other_img = WorkerWorkImage.objects.create(
            worker=self.other_worker_profile,
            image='portfolio/sample.jpg',
            sort_order=0
        )
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.delete(f'/api/workers/profile/work-images/{other_img.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_no_images_rejected(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post('/api/workers/profile/work-images/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_exceeding_max_images_limit(self):
        self.client.force_authenticate(user=self.worker_user)
        # Create 8 images already
        for i in range(8):
            WorkerWorkImage.objects.create(worker=self.worker_profile, image=f'portfolio/{i}.jpg', sort_order=i)

        dummy_img = create_dummy_image('JPEG')
        res = self.client.post(
            '/api/workers/profile/work-images/',
            {'images': [dummy_img]},
            format='multipart'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('up to 8', res.data['error'])
