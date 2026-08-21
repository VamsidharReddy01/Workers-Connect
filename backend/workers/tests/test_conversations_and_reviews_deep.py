from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from workers.models import Booking, WorkerProfile, Conversation, Message, BookingReview


class ConversationsAndReviewsDeepTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username='deep_cust', email='dc@example.com', password='Password123!', role='customer')
        self.other_cust = User.objects.create_user(username='other_dc', email='odc@example.com', password='Password123!', role='customer')
        self.worker_user = User.objects.create_user(username='deep_work', email='dw@example.com', password='Password123!', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Plumber', price=50.00, is_online=True)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='123 Deep St',
            scheduled_at=timezone.now(),
            total_amount=100.00,
            status=Booking.STATUS_COMPLETED
        )
        self.conversation = Conversation.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile
        )

    # ── Review Edge Cases ─────────────────────────────────────────────────────
    def test_review_rating_minimum_boundary_1(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{self.booking.id}/review/', {'rating': 1, 'feedback': 'Poor'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_profile.rating, 1.0)

    def test_review_rating_maximum_boundary_5(self):
        b2 = Booking.objects.create(
            customer=self.customer, worker=self.worker_profile, service_category='Plumber',
            address='Addr', scheduled_at=timezone.now(), total_amount=50.0, status=Booking.STATUS_COMPLETED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{b2.id}/review/', {'rating': 5, 'feedback': 'Perfect'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_review_missing_feedback_allowed(self):
        b3 = Booking.objects.create(
            customer=self.customer, worker=self.worker_profile, service_category='Plumber',
            address='Addr', scheduled_at=timezone.now(), total_amount=50.0, status=Booking.STATUS_COMPLETED
        )
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/bookings/{b3.id}/review/', {'rating': 4})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_review_non_existent_booking(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.post('/api/workers/bookings/999999/review/', {'rating': 5})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_review_other_customer_booking_rejected(self):
        self.client.force_authenticate(user=self.other_cust)
        res = self.client.post(f'/api/workers/bookings/{self.booking.id}/review/', {'rating': 5})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_worker_cannot_review_own_booking(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.post(f'/api/workers/bookings/{self.booking.id}/review/', {'rating': 5})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Conversation Edge Cases ───────────────────────────────────────────────
    def test_conversation_list_for_customer(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/workers/conversations/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)

    def test_conversation_list_for_worker(self):
        self.client.force_authenticate(user=self.worker_user)
        res = self.client.get('/api/workers/conversations/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)

    def test_conversation_messages_empty_thread(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.get(f'/api/workers/conversations/{self.conversation.id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 0)

    def test_conversation_messages_mark_unread_as_read(self):
        Message.objects.create(conversation=self.conversation, sender=self.worker_user, text='Message 1', is_read=False)
        Message.objects.create(conversation=self.conversation, sender=self.worker_user, text='Message 2', is_read=False)

        self.client.force_authenticate(user=self.customer)
        res = self.client.get(f'/api/workers/conversations/{self.conversation.id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 2)
        # All messages from worker should now be marked as read
        self.assertEqual(Message.objects.filter(conversation=self.conversation, is_read=False).count(), 0)

    def test_post_message_updates_conversation_timestamp(self):
        old_updated_at = self.conversation.updated_at
        self.client.force_authenticate(user=self.customer)
        res = self.client.post(f'/api/workers/conversations/{self.conversation.id}/messages/', {'text': 'Ping!'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.updated_at >= old_updated_at)

    def test_post_message_nonexistent_conversation(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.post('/api/workers/conversations/999999/messages/', {'text': 'Ping!'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_messages_nonexistent_conversation(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/workers/conversations/999999/messages/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
