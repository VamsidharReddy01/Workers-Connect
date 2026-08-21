from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from workers.models import JobCategory, WorkerProfile
from workers.views import _haversine_km


class WorkerSearchAndFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed sample workers in various locations & categories
        locations = [
            ('w_delhi', 'Electrician', 'Delhi', 28.6139, 77.2090, 100.0, True, 5.0),
            ('w_mumbai', 'Plumber', 'Mumbai', 19.0760, 72.8777, 80.0, True, 4.7),
            ('w_bangalore', 'Carpenter', 'Bangalore', 12.9716, 77.5946, 120.0, False, 4.9),
            ('w_hyderabad1', 'Painter', 'Hyderabad Hitech City', 17.4435, 78.3772, 60.0, True, 4.5),
            ('w_hyderabad2', 'Electrician', 'Hyderabad Secunderabad', 17.4399, 78.4983, 90.0, False, 4.8),
            ('w_kolkata', 'House Cleaner', 'Kolkata', 22.5726, 88.3639, 50.0, True, 4.2),
            ('w_chennai', 'AC Repair', 'Chennai', 13.0827, 80.2707, 110.0, True, 4.6),
            ('w_pune', 'Gardener', 'Pune', 18.5204, 73.8567, 70.0, True, 4.4),
        ]

        for uname, cat, loc, lat, lng, price, online, rating in locations:
            u = User.objects.create_user(
                username=uname,
                email=f'{uname}@example.com',
                password='Password123!',
                role='worker',
                location=loc,
                latitude=lat,
                longitude=lng
            )
            WorkerProfile.objects.create(
                user=u,
                category=cat,
                price=price,
                is_online=online,
                rating=rating,
                total_reviews=50
            )

    def test_filter_by_category_exact(self):
        res = self.client.get('/api/workers/nearby/?category=Electrician')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for w in res.data['list']:
            self.assertEqual(w['category'], 'Electrician')

    def test_filter_by_category_case_insensitive(self):
        res = self.client.get('/api/workers/nearby/?category=electrician')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data['list']) >= 2)

    def test_filter_by_available_only_true(self):
        res = self.client.get('/api/workers/nearby/?available_only=true')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for w in res.data['list']:
            self.assertTrue(w['is_online'])

    def test_filter_by_available_only_flag_1(self):
        res = self.client.get('/api/workers/nearby/?available_only=1')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for w in res.data['list']:
            self.assertTrue(w['is_online'])

    def test_filter_by_available_only_flag_yes(self):
        res = self.client.get('/api/workers/nearby/?available_only=yes')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for w in res.data['list']:
            self.assertTrue(w['is_online'])

    def test_search_by_worker_username(self):
        res = self.client.get('/api/workers/nearby/?search=w_delhi')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)
        self.assertEqual(res.data['list'][0]['user']['username'], 'w_delhi')

    def test_search_by_location_substring(self):
        res = self.client.get('/api/workers/nearby/?search=Secunderabad')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)
        self.assertEqual(res.data['list'][0]['user']['username'], 'w_hyderabad2')

    def test_search_by_category_substring(self):
        res = self.client.get('/api/workers/nearby/?search=Cleaner')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 1)
        self.assertEqual(res.data['list'][0]['category'], 'House Cleaner')

    def test_search_no_match_returns_empty_list(self):
        res = self.client.get('/api/workers/nearby/?search=NonExistentWorkerOrCategory123')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 0)

    def test_geospatial_sorting_closest_first(self):
        # Searching from Hyderabad Hitech City (17.4435, 78.3772)
        res = self.client.get('/api/workers/nearby/?lat=17.4435&lng=78.3772')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Nearest available should be w_hyderabad1 (0.0 km)
        nearest = res.data['list'][0]
        self.assertEqual(nearest['user']['username'], 'w_hyderabad1')
        self.assertEqual(nearest['distance_km'], 0.0)

    def test_haversine_across_equator(self):
        # 5 degrees North to 5 degrees South along prime meridian
        dist = _haversine_km(5.0, 0.0, -5.0, 0.0)
        self.assertTrue(1100 < dist < 1120)

    def test_haversine_across_international_dateline(self):
        # 0 lat, 179 lon to 0 lat, -179 lon (~222 km apart)
        dist = _haversine_km(0.0, 179.0, 0.0, -179.0)
        self.assertTrue(220 < dist < 225)
