from django.test import TestCase, RequestFactory
from accounts.backends import EmailBackend
from accounts.models import User


class EmailBackendTests(TestCase):
    def setUp(self):
        self.backend = EmailBackend()
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@example.com',
            password='CorrectPassword123!'
        )

    def test_authenticate_success_with_exact_email(self):
        user = self.backend.authenticate(
            self.request,
            username='auth@example.com',
            password='CorrectPassword123!'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_fails_with_wrong_password(self):
        user = self.backend.authenticate(
            self.request,
            username='auth@example.com',
            password='WrongPassword123!'
        )
        self.assertIsNone(user)

    def test_authenticate_fails_with_nonexistent_email(self):
        user = self.backend.authenticate(
            self.request,
            username='doesnotexist@example.com',
            password='CorrectPassword123!'
        )
        self.assertIsNone(user)

    def test_authenticate_with_none_password(self):
        user = self.backend.authenticate(
            self.request,
            username='auth@example.com',
            password=None
        )
        self.assertIsNone(user)

    def test_authenticate_with_none_username(self):
        user = self.backend.authenticate(
            self.request,
            username=None,
            password='CorrectPassword123!'
        )
        self.assertIsNone(user)

    def test_authenticate_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        # In Django ModelBackend, authenticate still returns the user object (views check is_active)
        user = self.backend.authenticate(
            self.request,
            username='auth@example.com',
            password='CorrectPassword123!'
        )
        self.assertEqual(user, self.user)
