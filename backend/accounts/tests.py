from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthViewsTests(APITestCase):
    def test_signup_returns_tokens_and_user(self):
        otp_response = self.client.post(reverse('send_signup_otp'), {
            'email': 'newuser@example.com',
        }, format='json')
        self.assertEqual(otp_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        otp = mail.outbox[0].body.split(' is ')[1].split('.')[0]

        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpass123',
            'role': 'customer',
            'phone_number': '+919876543210',
            'email_otp': otp,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertEqual(response.data['user']['role'], 'customer')

    def test_signup_requires_email_otp(self):
        response = self.client.post(reverse('signup'), {
            'username': 'nootpuser',
            'email': 'nootp@example.com',
            'password': 'strongpass123',
            'role': 'customer',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='nootp@example.com').exists())

    def test_login_returns_tokens_and_user(self):
        User.objects.create_user(
            username='loginuser',
            email='loginuser@example.com',
            password='strongpass123',
            role='worker',
        )

        response = self.client.post(reverse('login'), {
            'email': 'loginuser@example.com',
            'password': 'strongpass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['role'], 'worker')

    def test_profile_get_and_patch_require_authentication(self):
        user = User.objects.create_user(
            username='profileuser',
            email='profileuser@example.com',
            password='strongpass123',
            role='customer',
        )
        self.client.force_authenticate(user=user)

        get_response = self.client.get(reverse('profile'))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['email'], 'profileuser@example.com')

        patch_response = self.client.patch(reverse('profile'), {
            'username': 'updateduser',
            'role': 'worker',
        }, format='json')

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data['username'], 'updateduser')
        self.assertEqual(patch_response.data['role'], 'customer')

    def test_logout_requires_refresh_token(self):
        user = User.objects.create_user(
            username='logoutuser',
            email='logoutuser@example.com',
            password='strongpass123',
            role='customer',
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(reverse('logout'), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Refresh token is required')
