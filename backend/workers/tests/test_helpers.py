from django.test import TestCase
from accounts.models import User
from workers.models import JobCategory, WorkerProfile, Booking, BookingReview
from workers.views import _haversine_km, _category_list_payload, _recalculate_worker_rating, _ensure_job_categories


class WorkerHelperFunctionsTests(TestCase):
    def test_haversine_same_coordinates(self):
        dist = _haversine_km(17.3850, 78.4867, 17.3850, 78.4867)
        self.assertEqual(dist, 0.0)

    def test_haversine_known_distance(self):
        # Hyderabad (17.3850, 78.4867) to Bengaluru (12.9716, 77.5946) ~ 500 km
        dist = _haversine_km(17.3850, 78.4867, 12.9716, 77.5946)
        self.assertTrue(480 < dist < 520)

    def test_haversine_none_inputs(self):
        self.assertIsNone(_haversine_km(None, 78.48, 17.38, 78.48))
        self.assertIsNone(_haversine_km(17.38, None, 17.38, 78.48))
        self.assertIsNone(_haversine_km(17.38, 78.48, None, 78.48))
        self.assertIsNone(_haversine_km(17.38, 78.48, 17.38, None))

    def test_haversine_invalid_types(self):
        self.assertIsNone(_haversine_km('invalid', 'coordinates', 17.38, 78.48))

    def test_ensure_job_categories(self):
        JobCategory.objects.all().delete()
        _ensure_job_categories()
        self.assertTrue(JobCategory.objects.count() >= 10)
        # Calling again should not create duplicates
        _ensure_job_categories()
        self.assertEqual(JobCategory.objects.filter(name='Electrician').count(), 1)

    def test_recalculate_worker_rating_with_no_reviews(self):
        user = User.objects.create_user(username='rate_work', email='rw@example.com', password='pwd', role='worker')
        profile = WorkerProfile.objects.create(user=user, category='Plumber', price=30.00)
        _recalculate_worker_rating(profile)
        profile.refresh_from_db()
        self.assertEqual(profile.rating, 4.8)
        self.assertEqual(profile.total_reviews, 0)

    def test_category_list_payload(self):
        u1 = User.objects.create_user(username='u_cat1', email='uc1@example.com', password='pwd', role='worker')
        WorkerProfile.objects.create(user=u1, category='Carpenter', price=40.00, is_online=True)
        payload = _category_list_payload()
        self.assertTrue(any(item['category'] == 'Carpenter' for item in payload))
