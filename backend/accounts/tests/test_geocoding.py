import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from accounts.models import User


MOCK_REVERSE_RESPONSE = {
    'results': [{
        'formatted': 'Madhapur, Hyderabad, Telangana, India',
        'lat': 17.4486,
        'lon': 78.3908,
        'city': 'Hyderabad',
        'state': 'Telangana',
        'country': 'India',
    }]
}

MOCK_FORWARD_RESPONSE = {
    'results': [{
        'formatted': 'Madhapur, Hyderabad, Telangana, India',
        'lat': 17.4486,
        'lon': 78.3908,
    }]
}


@override_settings(GEOAPIFY_API_KEY='test_api_key_123')
class GeocodingServiceTest(TestCase):
    """Unit tests for the geocoding service functions."""

    @patch('accounts.services.geocoding.requests.get')
    def test_reverse_geocode_success(self, mock_get):
        from accounts.services.geocoding import reverse_geocode
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_REVERSE_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = reverse_geocode(17.4486, 78.3908)
        self.assertIsNotNone(result)
        self.assertEqual(result['location_name'], 'Madhapur, Hyderabad, Telangana, India')
        self.assertEqual(result['latitude'], 17.4486)
        self.assertEqual(result['longitude'], 78.3908)

    @patch('accounts.services.geocoding.requests.get')
    def test_reverse_geocode_no_results(self, mock_get):
        from accounts.services.geocoding import reverse_geocode
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = reverse_geocode(17.4486, 78.3908)
        self.assertIsNone(result)

    def test_reverse_geocode_invalid_coordinates(self):
        from accounts.services.geocoding import reverse_geocode
        self.assertIsNone(reverse_geocode(200, 78.3908))
        self.assertIsNone(reverse_geocode(17.4486, 300))
        self.assertIsNone(reverse_geocode(-91, 78.3908))
        self.assertIsNone(reverse_geocode('abc', 78.3908))

    @patch('accounts.services.geocoding.requests.get')
    def test_reverse_geocode_timeout(self, mock_get):
        import requests as req
        from accounts.services.geocoding import reverse_geocode
        mock_get.side_effect = req.exceptions.Timeout('Connection timed out')
        result = reverse_geocode(17.4486, 78.3908)
        self.assertIsNone(result)

    @patch('accounts.services.geocoding.requests.get')
    def test_reverse_geocode_api_error(self, mock_get):
        import requests as req
        from accounts.services.geocoding import reverse_geocode
        mock_get.side_effect = req.exceptions.HTTPError('500 Server Error')
        result = reverse_geocode(17.4486, 78.3908)
        self.assertIsNone(result)

    @patch('accounts.services.geocoding.requests.get')
    def test_forward_geocode_success(self, mock_get):
        from accounts.services.geocoding import forward_geocode
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_FORWARD_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = forward_geocode('Madhapur, Hyderabad')
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['latitude'], 17.4486, places=4)
        self.assertAlmostEqual(result['longitude'], 78.3908, places=4)

    @patch('accounts.services.geocoding.requests.get')
    def test_forward_geocode_no_results(self, mock_get):
        from accounts.services.geocoding import forward_geocode
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = forward_geocode('Nonexistent Place XYZ')
        self.assertIsNone(result)

    def test_forward_geocode_empty_input(self):
        from accounts.services.geocoding import forward_geocode
        self.assertIsNone(forward_geocode(''))
        self.assertIsNone(forward_geocode('   '))
        self.assertIsNone(forward_geocode(None))

    @patch('accounts.services.geocoding.requests.get')
    def test_forward_geocode_timeout(self, mock_get):
        import requests as req
        from accounts.services.geocoding import forward_geocode
        mock_get.side_effect = req.exceptions.Timeout('Connection timed out')
        result = forward_geocode('Madhapur, Hyderabad')
        self.assertIsNone(result)

    @override_settings(GEOAPIFY_API_KEY='')
    def test_geocode_no_api_key(self):
        from accounts.services.geocoding import reverse_geocode, forward_geocode
        self.assertIsNone(reverse_geocode(17.4486, 78.3908))
        self.assertIsNone(forward_geocode('Madhapur'))


@override_settings(GEOAPIFY_API_KEY='test_api_key_123')
class GeocodeLookupViewTest(TestCase):
    """Tests for the public geocode lookup endpoint."""

    def setUp(self):
        self.client = APIClient()

    @patch('accounts.views.reverse_geocode')
    def test_reverse_geocode_endpoint(self, mock_reverse):
        mock_reverse.return_value = {
            'location_name': 'Madhapur, Hyderabad, Telangana, India',
            'latitude': 17.4486,
            'longitude': 78.3908,
        }
        response = self.client.post(
            '/api/auth/geocode/',
            {'latitude': 17.4486, 'longitude': 78.3908},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location_name'], 'Madhapur, Hyderabad, Telangana, India')

    @patch('accounts.views.forward_geocode')
    def test_forward_geocode_endpoint(self, mock_forward):
        mock_forward.return_value = {
            'location_name': 'Madhapur, Hyderabad, Telangana, India',
            'latitude': 17.4486,
            'longitude': 78.3908,
        }
        response = self.client.post(
            '/api/auth/geocode/',
            {'location_name': 'Madhapur, Hyderabad'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('latitude', response.data)

    def test_geocode_endpoint_no_input(self):
        response = self.client.post('/api/auth/geocode/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_geocode_invalid_coordinates(self):
        response = self.client.post(
            '/api/auth/geocode/',
            {'latitude': 200, 'longitude': 78.3908},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_geocode_invalid_coordinate_type(self):
        response = self.client.post(
            '/api/auth/geocode/',
            {'latitude': 'abc', 'longitude': 78.3908},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(GEOAPIFY_API_KEY='test_api_key_123')
class UpdateLocationViewTest(TestCase):
    """Tests for the authenticated location update endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123!',
            role='customer',
        )
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self):
        client = APIClient()
        response = client.patch(
            '/api/auth/location/',
            {'latitude': 17.4486, 'longitude': 78.3908, 'location_source': 'gps'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('accounts.views.reverse_geocode')
    def test_gps_location_update(self, mock_reverse):
        mock_reverse.return_value = {
            'location_name': 'Madhapur, Hyderabad, Telangana, India',
            'latitude': 17.4486,
            'longitude': 78.3908,
        }
        response = self.client.patch(
            '/api/auth/location/',
            {'latitude': 17.4486, 'longitude': 78.3908, 'location_source': 'gps'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location_source'], 'gps')
        self.assertEqual(response.data['location_name'], 'Madhapur, Hyderabad, Telangana, India')

        self.user.refresh_from_db()
        self.assertEqual(str(self.user.latitude), '17.448600')
        self.assertEqual(self.user.location_source, 'gps')

    @patch('accounts.views.forward_geocode')
    def test_manual_location_update(self, mock_forward):
        mock_forward.return_value = {
            'location_name': 'Vijayawada, Andhra Pradesh, India',
            'latitude': 16.5062,
            'longitude': 80.6480,
        }
        response = self.client.patch(
            '/api/auth/location/',
            {'location_name': 'Vijayawada', 'location_source': 'manual'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location_source'], 'manual')
        self.assertIsNotNone(response.data['latitude'])

    def test_no_input(self):
        response = self.client.patch('/api/auth/location/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_location_source(self):
        response = self.client.patch(
            '/api/auth/location/',
            {'latitude': 17.4, 'longitude': 78.3, 'location_source': 'invalid'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_coordinates(self):
        response = self.client.patch(
            '/api/auth/location/',
            {'latitude': 200, 'longitude': 78.3908, 'location_source': 'gps'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_only_update_own_location(self):
        """Ensure the endpoint always updates the authenticated user's location."""
        other_user = User.objects.create_user(
            username='other', email='other@example.com', password='testpass123!'
        )
        with patch('accounts.views.reverse_geocode') as mock_reverse:
            mock_reverse.return_value = {
                'location_name': 'Test Location',
                'latitude': 17.4486,
                'longitude': 78.3908,
            }
            self.client.patch(
                '/api/auth/location/',
                {'latitude': 17.4486, 'longitude': 78.3908, 'location_source': 'gps'},
                format='json',
            )
        self.user.refresh_from_db()
        other_user.refresh_from_db()
        self.assertIsNotNone(self.user.latitude)
        self.assertIsNone(other_user.latitude)


@override_settings(GEOAPIFY_API_KEY='test_api_key_123')
class SignupLocationTest(TestCase):
    """Tests for geocoding during user signup."""

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    @patch('accounts.services.geocoding.reverse_geocode')
    def test_signup_with_gps_reverse_geocodes(self, mock_reverse):
        mock_reverse.return_value = {
            'location_name': 'Madhapur, Hyderabad, Telangana, India',
            'latitude': 17.4486,
            'longitude': 78.3908,
        }
        cache.set('signup_email_otp:gpsuser@example.com', '123456', timeout=600)

        response = self.client.post('/api/auth/signup/', {
            'username': 'gpsuser',
            'email': 'gpsuser@example.com',
            'password': 'SecurePassword123!',
            'latitude': 17.4486,
            'longitude': 78.3908,
            'location_permission_granted': True,
            'location_source': 'gps',
            'email_otp': '123456',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='gpsuser@example.com')
        self.assertEqual(user.location, 'Madhapur, Hyderabad, Telangana, India')
        self.assertEqual(user.location_source, 'gps')
        self.assertTrue(user.location_permission_granted)

    @patch('accounts.services.geocoding.forward_geocode')
    def test_signup_with_manual_forward_geocodes(self, mock_forward):
        mock_forward.return_value = {
            'location_name': 'Gachibowli, Hyderabad, Telangana, India',
            'latitude': 17.4401,
            'longitude': 78.3489,
        }
        cache.set('signup_email_otp:manualuser@example.com', '123456', timeout=600)

        response = self.client.post('/api/auth/signup/', {
            'username': 'manualuser',
            'email': 'manualuser@example.com',
            'password': 'SecurePassword123!',
            'location': 'Gachibowli, Hyderabad',
            'location_source': 'manual',
            'email_otp': '123456',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='manualuser@example.com')
        self.assertEqual(user.location, 'Gachibowli, Hyderabad, Telangana, India')
        self.assertEqual(user.location_source, 'manual')
        self.assertAlmostEqual(float(user.latitude), 17.4401, places=4)
        self.assertAlmostEqual(float(user.longitude), 78.3489, places=4)
