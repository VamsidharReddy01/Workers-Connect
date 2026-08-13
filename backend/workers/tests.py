from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Booking, Conversation, Message, WorkerProfile


class CustomerBrowseEndpointTests(APITestCase):
    def setUp(self):
        self.electrician = User.objects.create_user(
            username='ravi_electric',
            email='ravi@example.com',
            password='password123',
            role='worker',
            location='Hyderabad',
        )
        self.offline_electrician = User.objects.create_user(
            username='kiran_electric',
            email='kiran@example.com',
            password='password123',
            role='worker',
            location='Secunderabad',
        )
        self.custom_worker = User.objects.create_user(
            username='maya_solar',
            email='maya@example.com',
            password='password123',
            role='worker',
            location='Vijayawada',
        )
        self.customer = User.objects.create_user(
            username='customer_user',
            email='customer@example.com',
            password='password123',
            role='customer',
        )

        WorkerProfile.objects.create(
            user=self.electrician,
            category='Electrician',
            price=500,
            is_online=True,
        )
        WorkerProfile.objects.create(
            user=self.offline_electrician,
            category='Electrician',
            price=450,
            is_online=False,
        )
        WorkerProfile.objects.create(
            user=self.custom_worker,
            category='Solar Technician',
            price=800,
            is_online=True,
        )

    def test_categories_are_grouped_from_worker_registrations(self):
        response = self.client.get(reverse('worker-categories'))

        self.assertEqual(response.status_code, 200)
        categories = {item['category']: item for item in response.data['list']}

        self.assertEqual(categories['Electrician']['worker_count'], 2)
        self.assertEqual(categories['Electrician']['online_worker_count'], 1)
        self.assertEqual(categories['Solar Technician']['worker_count'], 1)
        self.assertNotIn('Plumber', categories)

    def test_nearby_workers_returns_registered_workers_ordered_by_availability(self):
        response = self.client.get(reverse('worker-nearby'))

        self.assertEqual(response.status_code, 200)
        workers = response.data['list']

        self.assertEqual(len(workers), 3)
        self.assertTrue(workers[0]['is_online'])
        self.assertTrue(workers[1]['is_online'])
        self.assertFalse(workers[2]['is_online'])
        self.assertEqual(workers[2]['user']['username'], 'kiran_electric')

    def test_nearby_workers_can_still_filter_to_available_workers(self):
        response = self.client.get(reverse('worker-nearby'), {'available_only': 'true'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['list']), 2)
        self.assertTrue(all(worker['is_online'] for worker in response.data['list']))

    def test_non_worker_users_are_not_returned_without_worker_profiles(self):
        response = self.client.get(reverse('worker-nearby'), {'search': self.customer.username})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['list'], [])


class BookingWorkflowTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer_booking',
            email='customer-booking@example.com',
            password='password123',
            role='customer',
            location='Hyderabad',
        )
        self.worker_user = User.objects.create_user(
            username='worker_booking',
            email='worker-booking@example.com',
            password='password123',
            role='worker',
            location='Hyderabad',
        )
        self.worker = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Plumber',
            price=700,
            is_online=True,
        )

    def create_booking(self):
        self.client.force_authenticate(user=self.customer)
        return self.client.post(reverse('customer-booking-create'), {
            'worker_id': self.worker.id,
            'service_category': 'Plumber',
            'description': 'Fix a leaking sink',
            'address': '123 Home Street',
            'scheduled_at': timezone.now().isoformat(),
            'total_amount': '700.00',
        }, format='json')

    def test_customer_can_create_booking_and_conversation(self):
        response = self.create_booking()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)

    def test_worker_can_update_allowed_booking_status(self):
        booking_id = self.create_booking().data['id']
        self.client.force_authenticate(user=self.worker_user)

        response = self.client.patch(reverse('worker-booking-status', args=[booking_id]), {
            'status': Booking.STATUS_ACCEPTED,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], Booking.STATUS_ACCEPTED)

    def test_worker_status_flow_rejects_invalid_shortcuts(self):
        booking_id = self.create_booking().data['id']
        self.client.force_authenticate(user=self.worker_user)

        requested_to_completed = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_COMPLETED},
            format='json',
        )
        self.assertEqual(requested_to_completed.status_code, 400)

        accepted = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_ACCEPTED},
            format='json',
        )
        accepted_to_completed = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_COMPLETED},
            format='json',
        )
        accepted_to_start = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_IN_PROGRESS},
            format='json',
        )

        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted_to_completed.status_code, 400)
        self.assertEqual(accepted_to_start.status_code, 400)

    def test_worker_status_flow_allows_each_required_step(self):
        booking_id = self.create_booking().data['id']
        self.client.force_authenticate(user=self.worker_user)

        for next_status in [
            Booking.STATUS_ACCEPTED,
            Booking.STATUS_ON_THE_WAY,
            Booking.STATUS_IN_PROGRESS,
            Booking.STATUS_COMPLETED,
        ]:
            response = self.client.patch(
                reverse('worker-booking-status', args=[booking_id]),
                {'status': next_status},
                format='json',
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['status'], next_status)

    def test_worker_can_decline_requested_booking_only_once(self):
        booking_id = self.create_booking().data['id']
        self.client.force_authenticate(user=self.worker_user)

        declined = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_DECLINED},
            format='json',
        )
        reopen = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_ACCEPTED},
            format='json',
        )

        self.assertEqual(declined.status_code, 200)
        self.assertEqual(reopen.status_code, 400)

    def test_other_worker_cannot_update_booking_status(self):
        booking_id = self.create_booking().data['id']
        other_user = User.objects.create_user(
            username='other_worker',
            email='other-worker@example.com',
            password='password123',
            role='worker',
        )
        WorkerProfile.objects.create(
            user=other_user,
            category='Painter',
            price=500,
            is_online=True,
        )
        self.client.force_authenticate(user=other_user)

        response = self.client.patch(
            reverse('worker-booking-status', args=[booking_id]),
            {'status': Booking.STATUS_ACCEPTED},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_customer_can_review_completed_booking_once(self):
        booking_id = self.create_booking().data['id']
        booking = Booking.objects.get(id=booking_id)
        booking.status = Booking.STATUS_COMPLETED
        booking.save(update_fields=['status'])
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(reverse('booking-review', args=[booking_id]), {
            'rating': 5,
            'feedback': 'Excellent work.',
        }, format='json')
        duplicate = self.client.post(reverse('booking-review', args=[booking_id]), {
            'rating': 5,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(duplicate.status_code, 400)

    def test_conversation_access_is_limited_to_participants(self):
        booking_id = self.create_booking().data['id']
        conversation_id = Booking.objects.get(id=booking_id).conversation.id
        stranger = User.objects.create_user(
            username='stranger',
            email='stranger@example.com',
            password='password123',
            role='customer',
        )
        self.client.force_authenticate(user=stranger)

        response = self.client.get(reverse('conversation-messages', args=[conversation_id]))

        self.assertEqual(response.status_code, 403)


class WorkerPortfolioTests(APITestCase):
    def setUp(self):
        self.worker_user = User.objects.create_user(
            username='portfolio_worker',
            email='portfolio@example.com',
            password='password123',
            role='worker',
        )
        self.worker = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Carpenter',
            price=900,
            is_online=True,
        )
        self.client.force_authenticate(user=self.worker_user)

    def test_worker_can_upload_and_delete_portfolio_image(self):
        image = SimpleUploadedFile(
            'work.png',
            b'\x89PNG\r\n\x1a\n' + b'0' * 128,
            content_type='image/png',
        )

        upload = self.client.post(reverse('worker-work-images'), {
            'images': image,
            'caption': 'Recent work',
        }, format='multipart')
        image_id = upload.data['list'][0]['id']
        delete = self.client.delete(reverse('worker-work-image-delete', args=[image_id]))

        self.assertEqual(upload.status_code, 201)
        self.assertEqual(delete.status_code, 204)

    def test_worker_portfolio_rejects_invalid_file_type(self):
        upload = SimpleUploadedFile(
            'work.txt',
            b'not an image',
            content_type='text/plain',
        )

        response = self.client.post(reverse('worker-work-images'), {
            'images': upload,
        }, format='multipart')

        self.assertEqual(response.status_code, 400)
