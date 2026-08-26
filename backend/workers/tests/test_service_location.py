from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from workers.models import Booking, WorkerProfile


@override_settings(GEOAPIFY_API_KEY='test_geoapify_key')
class BookingServiceLocationTest(TestCase):
    """Integration and unit tests for automatic service location in worker bookings."""

    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='cust1',
            email='cust1@example.com',
            password='Password123!',
            role='customer',
            location='Madhapur, Hyderabad, Telangana, India',
            latitude=Decimal('17.448600'),
            longitude=Decimal('78.390800'),
            location_source='saved',
        )
        self.worker_user = User.objects.create_user(
            username='work1',
            email='work1@example.com',
            password='Password123!',
            role='worker',
            location='Gachibowli, Hyderabad',
            latitude=Decimal('17.440100'),
            longitude=Decimal('78.348900'),
        )
        self.worker_profile = WorkerProfile.objects.create(
            user=self.worker_user,
            category='Carpenter',
            price=Decimal('50.00'),
            is_online=True,
        )
        self.client.force_authenticate(user=self.customer)

    def test_booking_with_saved_customer_location(self):
        """Booking created with customer's saved location source and coordinates."""
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Fix wooden table leg',
                'address': self.customer.location,
                'service_latitude': float(self.customer.latitude),
                'service_longitude': float(self.customer.longitude),
                'service_location_source': 'saved',
                'location_permission_granted': True,
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service_location_source'], 'saved')
        self.assertEqual(response.data['address'], 'Madhapur, Hyderabad, Telangana, India')
        self.assertEqual(str(response.data['service_latitude']), '17.448600')
        self.assertEqual(str(response.data['service_longitude']), '78.390800')

        booking = Booking.objects.get(id=response.data['id'])
        self.assertEqual(booking.service_location_source, 'saved')
        self.assertEqual(booking.address, 'Madhapur, Hyderabad, Telangana, India')

    def test_booking_with_gps_location(self):
        """Booking created with freshly captured GPS coordinates and source='gps'."""
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Fix kitchen door',
                'address': 'HITEC City, Hyderabad',
                'service_latitude': 17.4435,
                'service_longitude': 78.3772,
                'service_location_source': 'gps',
                'location_permission_granted': True,
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service_location_source'], 'gps')
        self.assertEqual(response.data['address'], 'HITEC City, Hyderabad')
        self.assertAlmostEqual(float(response.data['service_latitude']), 17.4435, places=4)
        self.assertAlmostEqual(float(response.data['service_longitude']), 78.3772, places=4)

    @patch('workers.serializers.forward_geocode')
    def test_booking_with_manual_address_auto_geocodes(self, mock_forward):
        """Manual address without coordinates triggers forward geocoding on backend."""
        mock_forward.return_value = {
            'location_name': 'Kondapur, Hyderabad, Telangana, India',
            'latitude': 17.4699,
            'longitude': 78.3578,
        }
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Assemble bed frame',
                'address': 'Kondapur, Hyderabad',
                'service_location_source': 'manual',
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service_location_source'], 'manual')
        self.assertEqual(response.data['address'], 'Kondapur, Hyderabad')
        self.assertAlmostEqual(float(response.data['service_latitude']), 17.4699, places=4)
        self.assertAlmostEqual(float(response.data['service_longitude']), 78.3578, places=4)

    @patch('workers.serializers.reverse_geocode')
    def test_booking_with_coordinates_and_empty_address_auto_reverse_geocodes(self, mock_reverse):
        """Booking with GPS coordinates but empty address auto reverse-geocodes address."""
        mock_reverse.return_value = {
            'location_name': 'Jubilee Hills, Hyderabad, Telangana, India',
            'latitude': 17.4319,
            'longitude': 78.4073,
        }
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Repair chairs',
                'address': '',
                'service_latitude': 17.4319,
                'service_longitude': 78.4073,
                'service_location_source': 'gps',
                'location_permission_granted': True,
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['address'], 'Jubilee Hills, Hyderabad, Telangana, India')

    def test_booking_snapshot_integrity_when_profile_changes(self):
        """Changing customer user location later must NOT modify existing booking's service location."""
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Initial booking at Madhapur',
                'address': 'Madhapur, Hyderabad',
                'service_latitude': 17.4486,
                'service_longitude': 78.3908,
                'service_location_source': 'saved',
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking_id = response.data['id']

        # Customer moves to a new city/location
        self.customer.location = 'Banjara Hills, Hyderabad'
        self.customer.latitude = Decimal('17.415600')
        self.customer.longitude = Decimal('78.435000')
        self.customer.save()

        # Check that the previous booking still has original Madhapur coordinates and address
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.address, 'Madhapur, Hyderabad')
        self.assertEqual(str(booking.service_latitude), '17.448600')
        self.assertEqual(str(booking.service_longitude), '78.390800')
        self.assertEqual(booking.service_location_source, 'saved')

    def test_invalid_coordinates_rejected(self):
        """Out of range latitude or longitude must be rejected with 400 Bad Request."""
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Invalid coords test',
                'address': 'Test Address',
                'service_latitude': 95.0,  # Invalid (>90)
                'service_longitude': 78.3908,
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_location_source_rejected(self):
        """Invalid service_location_source value must be rejected with 400 Bad Request."""
        scheduled = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/workers/bookings/create/',
            {
                'worker_id': self.worker_profile.id,
                'service_category': 'Carpenter',
                'description': 'Invalid source test',
                'address': 'Test Address',
                'service_latitude': 17.4486,
                'service_longitude': 78.3908,
                'service_location_source': 'invalid_source',
                'scheduled_at': scheduled,
                'total_amount': '50.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_worker_can_view_booking_with_service_location(self):
        """Worker retrieves booking list and sees full service location snapshot."""
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Carpenter',
            description='Check door hinge',
            address='Madhapur, Hyderabad',
            service_latitude=Decimal('17.448600'),
            service_longitude=Decimal('78.390800'),
            service_location_source='saved',
            location_permission_granted=True,
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            total_amount=Decimal('50.00'),
        )

        # Authenticate as worker
        self.client.force_authenticate(user=self.worker_user)
        response = self.client.get('/api/workers/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        worker_bookings = response.data['list']
        matching = [b for b in worker_bookings if b['id'] == booking.id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]['address'], 'Madhapur, Hyderabad')
        self.assertEqual(str(matching[0]['service_latitude']), '17.448600')
        self.assertEqual(str(matching[0]['service_longitude']), '78.390800')
        self.assertEqual(matching[0]['service_location_source'], 'saved')
