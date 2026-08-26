from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from workers.models import WorkerProfile


class NearbyWorkersDistanceTest(TestCase):
    """Integration and unit tests for Nearby Workers with Distance calculation and radius filtering."""

    def setUp(self):
        self.client = APIClient()

        # Customer in Madhapur, Hyderabad (17.4486, 78.3908)
        self.customer = User.objects.create_user(
            username='customer_madhapur',
            email='customer_m@example.com',
            password='Password123!',
            role='customer',
            location='Madhapur, Hyderabad, Telangana',
            latitude=Decimal('17.448600'),
            longitude=Decimal('78.390800'),
        )

        # Worker 1: Hitec City, Hyderabad (~1.5 km away) - Online Carpenter
        self.u1 = User.objects.create_user(
            username='ravi_kumar',
            email='ravi@example.com',
            password='Password123!',
            role='worker',
            location='HITEC City, Hyderabad',
            latitude=Decimal('17.443500'),
            longitude=Decimal('78.377200'),
        )
        self.w1 = WorkerProfile.objects.create(
            user=self.u1,
            category='Carpenter',
            price=Decimal('50.00'),
            is_online=True,
            rating=4.9,
            total_reviews=100,
        )

        # Worker 2: Gachibowli, Hyderabad (~5.0 km away) - Online Plumber
        self.u2 = User.objects.create_user(
            username='suresh_yadav',
            email='suresh@example.com',
            password='Password123!',
            role='worker',
            location='Gachibowli, Hyderabad',
            latitude=Decimal('17.440100'),
            longitude=Decimal('78.348900'),
        )
        self.w2 = WorkerProfile.objects.create(
            user=self.u2,
            category='Plumber',
            price=Decimal('45.00'),
            is_online=True,
            rating=4.7,
            total_reviews=80,
        )

        # Worker 3: Secunderabad (~15.0 km away) - Online Carpenter
        self.u3 = User.objects.create_user(
            username='dinesh_sharma',
            email='dinesh@example.com',
            password='Password123!',
            role='worker',
            location='Secunderabad, Telangana',
            latitude=Decimal('17.439900'),
            longitude=Decimal('78.498300'),
        )
        self.w3 = WorkerProfile.objects.create(
            user=self.u3,
            category='Carpenter',
            price=Decimal('60.00'),
            is_online=True,
            rating=4.8,
            total_reviews=50,
        )

        # Worker 4: Delhi (~1250 km away) - Online Carpenter
        self.u4 = User.objects.create_user(
            username='amit_singh',
            email='amit@example.com',
            password='Password123!',
            role='worker',
            location='Connaught Place, New Delhi',
            latitude=Decimal('28.630400'),
            longitude=Decimal('77.217700'),
        )
        self.w4 = WorkerProfile.objects.create(
            user=self.u4,
            category='Carpenter',
            price=Decimal('40.00'),
            is_online=True,
            rating=4.5,
            total_reviews=30,
        )

        # Worker 5: No coordinates - Offline Electrician
        self.u5 = User.objects.create_user(
            username='nocoord_worker',
            email='nocoord@example.com',
            password='Password123!',
            role='worker',
            location='Unknown Area',
            latitude=None,
            longitude=None,
        )
        self.w5 = WorkerProfile.objects.create(
            user=self.u5,
            category='Electrician',
            price=Decimal('55.00'),
            is_online=False,
            rating=4.0,
            total_reviews=10,
        )

    def test_authenticated_customer_saved_coordinates_used_automatically(self):
        """Authenticated customer gets workers sorted by distance from their saved coordinates."""
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/workers/nearby/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data['list']
        self.assertTrue(len(data) >= 4)

        # Nearest available worker should be w1 (~1.5 km)
        self.assertEqual(data[0]['id'], self.w1.id)
        self.assertIsNotNone(data[0]['distance_km'])
        self.assertAlmostEqual(data[0]['distance_km'], 1.54, delta=0.5)

        # Second nearest available should be w2 (~4.5 km)
        self.assertEqual(data[1]['id'], self.w2.id)
        self.assertAlmostEqual(data[1]['distance_km'], 4.54, delta=1.0)

        # Third nearest should be w3 (~12 km)
        self.assertEqual(data[2]['id'], self.w3.id)
        self.assertTrue(data[2]['distance_km'] > data[1]['distance_km'])

        # Farthest should be w4 (Delhi > 1000 km)
        self.assertEqual(data[3]['id'], self.w4.id)
        self.assertTrue(data[3]['distance_km'] > 1000)

        # Worker without coords should have distance_km: None
        w5_data = next((x for x in data if x['id'] == self.w5.id), None)
        self.assertIsNotNone(w5_data)
        self.assertIsNone(w5_data['distance_km'])

    def test_worker_response_schema_fields(self):
        """Every worker object in response contains name, latitude, longitude, location_name, and distance_km."""
        res = self.client.get('/api/workers/nearby/?lat=17.4486&lng=78.3908')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        w1_data = next(x for x in res.data['list'] if x['id'] == self.w1.id)
        self.assertEqual(w1_data['name'], 'ravi_kumar')
        self.assertEqual(w1_data['location_name'], 'HITEC City, Hyderabad')
        self.assertAlmostEqual(float(w1_data['latitude']), 17.4435, places=4)
        self.assertAlmostEqual(float(w1_data['longitude']), 78.3772, places=4)
        self.assertIsNotNone(w1_data['distance_km'])

    def test_radius_filtering_10km(self):
        """Radius=10 filter only includes workers within 10 km."""
        res = self.client.get('/api/workers/nearby/?lat=17.4486&lng=78.3908&radius=10')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ids = [w['id'] for w in res.data['list']]
        self.assertIn(self.w1.id, ids)  # ~1.5 km
        self.assertIn(self.w2.id, ids)  # ~4.5 km
        self.assertNotIn(self.w3.id, ids)  # ~12 km (> 10 km)
        self.assertNotIn(self.w4.id, ids)  # ~1250 km (> 10 km)
        self.assertNotIn(self.w5.id, ids)  # No coordinates

    def test_radius_and_category_filter(self):
        """Combining radius=20 and category=Carpenter returns only nearby carpenters."""
        res = self.client.get('/api/workers/nearby/?lat=17.4486&lng=78.3908&radius=20&category=Carpenter')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ids = [w['id'] for w in res.data['list']]
        self.assertIn(self.w1.id, ids)  # Carpenter within 20 km
        self.assertIn(self.w3.id, ids)  # Carpenter within 20 km
        self.assertNotIn(self.w2.id, ids)  # Plumber (excluded by category)
        self.assertNotIn(self.w4.id, ids)  # Carpenter in Delhi (excluded by radius)

    def test_zero_distance_same_location(self):
        """Exact same coordinates returns 0.0 distance."""
        res = self.client.get(f'/api/workers/nearby/?lat={self.u1.latitude}&lng={self.u1.longitude}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        nearest = res.data['list'][0]
        self.assertEqual(nearest['id'], self.w1.id)
        self.assertEqual(nearest['distance_km'], 0.0)

    def test_invalid_coordinates_rejected(self):
        """Invalid latitude (>90) or non-numeric returns 400 Bad Request."""
        res1 = self.client.get('/api/workers/nearby/?lat=95.0&lng=78.0')
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.get('/api/workers/nearby/?lat=invalid&lng=78.0')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        res3 = self.client.get('/api/workers/nearby/?lat=17.0&lng=200.0')
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_radius_rejected(self):
        """Invalid radius (<=0 or >1000 or non-numeric) returns 400 Bad Request."""
        res1 = self.client.get('/api/workers/nearby/?lat=17.44&lng=78.39&radius=-5')
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.get('/api/workers/nearby/?lat=17.44&lng=78.39&radius=5000')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        res3 = self.client.get('/api/workers/nearby/?lat=17.44&lng=78.39&radius=abc')
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_detail_with_distance(self):
        """Worker public detail endpoint calculates distance when coordinates provided."""
        res = self.client.get(f'/api/workers/{self.w1.id}/?lat=17.4486&lng=78.3908')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'ravi_kumar')
        self.assertEqual(res.data['location_name'], 'HITEC City, Hyderabad')
        self.assertIsNotNone(res.data['distance_km'])
        self.assertAlmostEqual(res.data['distance_km'], 1.54, delta=0.5)

    def test_root_workers_alias_route(self):
        """GET /api/workers/ works identically to GET /api/workers/nearby/."""
        res = self.client.get('/api/workers/?lat=17.4486&lng=78.3908&radius=10')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 2)
        self.assertIn('results', res.data)
