from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from .models import WorkerProfile


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
