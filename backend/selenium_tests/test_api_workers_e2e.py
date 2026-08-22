import requests
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from selenium_tests.base import APIEndToEndTestCase, CUSTOMER_PASSWORD, WORKER_PASSWORD
from workers.models import Booking, Conversation, Message, BookingReview


class WorkersAPIEndToEndTests(APIEndToEndTestCase):
    def setUp(self):
        super().setUp()
        self.cat = self.create_category('Plumber', 1, True)
        self.worker_user, self.worker_profile = self.create_worker_with_profile('wrk', 'Plumber')
        self.worker_email = self.worker_user.email
        self.worker_pass = WORKER_PASSWORD
        self.customer = self.create_customer('cst')
        self.customer_email = self.customer.email
        self.customer_pass = CUSTOMER_PASSWORD
        self.w_acc, _ = self.login_api(self.worker_email, self.worker_pass)
        self.c_acc, _ = self.login_api(self.customer_email, self.customer_pass)

    def test_worker_profile_get(self):
        """1"""
        r = self.authenticated_get('/api/workers/profile/', self.w_acc)
        self.assertEqual(r.status_code, 200)

    def test_worker_profile_update_bio(self):
        """2"""
        r = self.authenticated_patch('/api/workers/profile/', self.w_acc, json={'bio': 'New Bio'})
        self.assertEqual(r.status_code, 200)

    def test_worker_profile_update_price(self):
        """3"""
        r = self.authenticated_patch('/api/workers/profile/', self.w_acc, json={'price': '75.00'})
        self.assertEqual(r.status_code, 200)

    def test_worker_profile_unauthenticated(self):
        """4"""
        r = self.http.get(self.api_url('/api/workers/profile/'))
        self.assertEqual(r.status_code, 401)

    def test_worker_availability_set_true(self):
        """5"""
        r = self.authenticated_patch('/api/workers/availability/', self.w_acc, json={'is_online': True})
        self.assertEqual(r.status_code, 200)

    def test_worker_availability_set_false(self):
        """6"""
        r = self.authenticated_patch('/api/workers/availability/', self.w_acc, json={'is_online': False})
        self.assertEqual(r.status_code, 200)


    def test_worker_dashboard_summary(self):
        """7"""
        r = self.authenticated_get('/api/workers/dashboard/', self.w_acc)
        self.assertEqual(r.status_code, 200)

    def test_worker_booking_list(self):
        """8"""
        r = self.authenticated_get('/api/workers/bookings/', self.w_acc)
        self.assertEqual(r.status_code, 200)

    def test_worker_booking_accept(self):
        """9"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        r = self.authenticated_patch(f'/api/workers/bookings/{b.id}/status/', self.w_acc, json={'status': 'accepted'})
        self.assertEqual(r.status_code, 200)

    def test_worker_booking_decline(self):
        """10"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        r = self.authenticated_patch(f'/api/workers/bookings/{b.id}/status/', self.w_acc, json={'status': 'declined'})
        self.assertEqual(r.status_code, 200)

    def test_worker_booking_complete(self):
        """11"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        for s in ['accepted', 'on_the_way', 'in_progress', 'completed']:
            self.authenticated_patch(f'/api/workers/bookings/{b.id}/status/', self.w_acc, json={'status': s})
        b.refresh_from_db()
        self.assertEqual(b.status, 'completed')

    def test_customer_booking_create(self):
        """12"""
        data = {
            'worker_id': self.worker_profile.id,
            'service_category': 'Plumber',
            'address': '123 Main St',
            'scheduled_at': '2030-01-01T10:00:00Z',
            'total_amount': '150.00',
            'description': 'Fix faucet',
        }
        r = self.authenticated_post('/api/workers/bookings/create/', self.c_acc, json=data)
        self.assertEqual(r.status_code, 201)

    def test_customer_booking_list(self):
        """13"""
        r = self.authenticated_get('/api/workers/bookings/my/', self.c_acc)
        self.assertEqual(r.status_code, 200)

    def test_customer_booking_cancel(self):
        """14"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        r = self.authenticated_post(f'/api/workers/bookings/{b.id}/cancel/', self.c_acc)
        self.assertIn(r.status_code, [200, 204, 201])

    def test_booking_review_create(self):
        """15"""
        b = self.create_booking(self.customer, self.worker_profile, 'completed')
        r = self.authenticated_post(f'/api/workers/bookings/{b.id}/review/', self.c_acc, json={'rating': 5, 'feedback': 'Great service!'})
        self.assertIn(r.status_code, [201, 200])

    def test_booking_review_rating_range(self):
        """16"""
        b = self.create_booking(self.customer, self.worker_profile, 'completed')
        r = self.authenticated_post(f'/api/workers/bookings/{b.id}/review/', self.c_acc, json={'rating': 6, 'feedback': 'Invalid rating'})
        self.assertEqual(r.status_code, 400)

    def test_conversation_list_customer(self):
        """17"""
        r = self.authenticated_get('/api/workers/conversations/', self.c_acc)
        self.assertEqual(r.status_code, 200)

    def test_conversation_list_worker(self):
        """18"""
        r = self.authenticated_get('/api/workers/conversations/', self.w_acc)
        self.assertEqual(r.status_code, 200)

    def test_conversation_send_message(self):
        """19"""
        b = self.create_booking(self.customer, self.worker_profile, 'accepted')
        conv = self.create_conversation(b, self.customer, self.worker_profile)
        r = self.authenticated_post(f'/api/workers/conversations/{conv.id}/messages/', self.c_acc, json={'text': 'Hello'})
        self.assertEqual(r.status_code, 201)

    def test_conversation_get_messages(self):
        """20"""
        b = self.create_booking(self.customer, self.worker_profile, 'accepted')
        conv = self.create_conversation(b, self.customer, self.worker_profile)
        r = self.authenticated_get(f'/api/workers/conversations/{conv.id}/messages/', self.c_acc)
        self.assertEqual(r.status_code, 200)

    def test_categories_list(self):
        """21"""
        r = self.http.get(self.api_url('/api/workers/categories/'))
        self.assertEqual(r.status_code, 200)

    def test_job_categories_list(self):
        """22"""
        r = self.http.get(self.api_url('/api/workers/job-categories/'))
        self.assertEqual(r.status_code, 200)

    def test_nearby_workers(self):
        """23"""
        r = self.http.get(self.api_url('/api/workers/nearby/?latitude=17.38&longitude=78.49'))
        self.assertEqual(r.status_code, 200)

    def test_nearby_workers_no_coords(self):
        """24"""
        r = self.http.get(self.api_url('/api/workers/nearby/'))
        self.assertIn(r.status_code, [200, 400])

    def test_worker_public_detail(self):
        """25"""
        r = self.http.get(self.api_url(f'/api/workers/{self.worker_profile.id}/'))
        self.assertEqual(r.status_code, 200)

    def test_worker_profile_create_new(self):
        """26"""
        u, p = self.create_worker('new_w', 'Electrician')
        a, _ = self.login_api(u.email, WORKER_PASSWORD)
        r = self.authenticated_patch('/api/workers/profile/', a, json={'bio': 'Hi'})
        self.assertEqual(r.status_code, 200)

    def test_booking_invalid_status_transition(self):
        """27"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        r = self.authenticated_patch(f'/api/workers/bookings/{b.id}/status/', self.w_acc, json={'status': 'completed'})
        self.assertEqual(r.status_code, 400)

    def test_customer_cannot_update_booking_status(self):
        """28"""
        b = self.create_booking(self.customer, self.worker_profile, 'requested')
        r = self.authenticated_patch(f'/api/workers/bookings/{b.id}/status/', self.c_acc, json={'status': 'accepted'})
        self.assertIn(r.status_code, [403, 404])


    def test_worker_booking_list_empty(self):
        """29"""
        r = self.authenticated_get('/api/workers/bookings/', self.w_acc)
        self.assertEqual(r.status_code, 200)

    def test_conversation_access_control(self):
        """30"""
        r = self.authenticated_get('/api/workers/conversations/999999/messages/', self.c_acc)
        self.assertEqual(r.status_code, 404)
