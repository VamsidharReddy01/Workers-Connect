import io
from PIL import Image
from django.test import TestCase, RequestFactory
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers
from accounts.models import User, SupportTicket
from accounts.serializers import (
    UserSerializer,
    PublicUserSerializer,
    SignupSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    SupportTicketSerializer,
    validate_latitude,
    validate_longitude,
    _validate_image_magic_bytes,
)


def create_dummy_image(format='JPEG', size=(50, 50)):
    file_obj = io.BytesIO()
    image = Image.new('RGB', size, color=(255, 0, 0))
    image.save(file_obj, format=format)
    file_obj.seek(0)
    return SimpleUploadedFile(f"test.{format.lower()}", file_obj.read(), content_type=f"image/{format.lower()}")


class AccountSerializerValidationHelperTests(TestCase):
    def test_validate_latitude_valid(self):
        self.assertEqual(validate_latitude(0), 0)
        self.assertEqual(validate_latitude(45.5), 45.5)
        self.assertEqual(validate_latitude(-90), -90)
        self.assertEqual(validate_latitude(90), 90)
        self.assertIsNone(validate_latitude(None))
        self.assertIsNone(validate_latitude(''))

    def test_validate_latitude_invalid_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_latitude(90.1)
        with self.assertRaises(serializers.ValidationError):
            validate_latitude(-90.1)

    def test_validate_longitude_valid(self):
        self.assertEqual(validate_longitude(0), 0)
        self.assertEqual(validate_longitude(180), 180)
        self.assertEqual(validate_longitude(-180), -180)
        self.assertIsNone(validate_longitude(None))
        self.assertIsNone(validate_longitude(''))

    def test_validate_longitude_invalid_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_longitude(180.1)
        with self.assertRaises(serializers.ValidationError):
            validate_longitude(-180.1)

    def test_validate_image_magic_bytes_valid_jpeg(self):
        valid_img = create_dummy_image('JPEG')
        result = _validate_image_magic_bytes(valid_img)
        self.assertIsNotNone(result)

    def test_validate_image_magic_bytes_valid_png(self):
        valid_img = create_dummy_image('PNG')
        result = _validate_image_magic_bytes(valid_img)
        self.assertIsNotNone(result)

    def test_validate_image_magic_bytes_invalid_content(self):
        fake_file = SimpleUploadedFile("shell.jpg", b"<?php phpinfo(); ?>", content_type="image/jpeg")
        with self.assertRaises(serializers.ValidationError):
            _validate_image_magic_bytes(fake_file)

    def test_validate_image_magic_bytes_none(self):
        self.assertIsNone(_validate_image_magic_bytes(None))


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user123',
            email='user123@example.com',
            password='Password123!',
            phone_number='1234567890',
            location='City Center'
        )

    def test_user_serializer_fields(self):
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'user123')
        self.assertEqual(data['email'], 'user123@example.com')
        self.assertEqual(data['phone_number'], '1234567890')
        self.assertEqual(data['location'], 'City Center')

    def test_username_min_length_validation(self):
        serializer = UserSerializer(instance=self.user, data={'username': 'ab'}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_username_unique_validation(self):
        User.objects.create_user(username='otheruser', email='other@example.com', password='pwd')
        serializer = UserSerializer(instance=self.user, data={'username': 'otheruser'}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_email_unique_case_insensitive(self):
        User.objects.create_user(username='otheruser', email='other@example.com', password='pwd')
        serializer = UserSerializer(instance=self.user, data={'email': 'OTHER@EXAMPLE.COM'}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_phone_number_unique_validation(self):
        User.objects.create_user(username='otheruser', email='other@example.com', password='pwd', phone_number='9999999999')
        serializer = UserSerializer(instance=self.user, data={'phone_number': '9999999999'}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

    def test_coordinates_must_be_provided_together(self):
        serializer = UserSerializer(instance=self.user, data={'latitude': 17.38}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('location', serializer.errors)

    def test_valid_profile_update(self):
        serializer = UserSerializer(
            instance=self.user,
            data={'location': 'New Area', 'latitude': 12.97, 'longitude': 77.59},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.location, 'New Area')
        self.assertIsNotNone(updated.location_updated_at)


class PublicUserSerializerTests(TestCase):
    def test_masks_sensitive_attributes(self):
        user = User.objects.create_user(
            username='publicuser',
            email='secret@example.com',
            password='pwd',
            phone_number='1122334455',
            location='Secret Address',
            latitude=17.38,
            longitude=78.48
        )
        serializer = PublicUserSerializer(user)
        data = serializer.data
        self.assertEqual(data['username'], 'publicuser')
        self.assertNotIn('email', data)
        self.assertNotIn('phone_number', data)
        self.assertNotIn('latitude', data)
        self.assertNotIn('longitude', data)
        self.assertIn('masked_location', data)


class SignupSerializerTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_signup_serializer_valid_data(self):
        cache.set('signup_email_otp:newuser@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:newuser@example.com', 0, timeout=600)
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!',
            'email_otp': '123456',
        }
        serializer = SignupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.role, 'customer')

    def test_signup_missing_otp(self):
        data = {
            'username': 'nootp',
            'email': 'nootp@example.com',
            'password': 'Password123!',
            'email_otp': '123456'
        }
        serializer = SignupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email_otp', serializer.errors)

    def test_signup_invalid_otp(self):
        cache.set('signup_email_otp:wrongotp@example.com', '654321', timeout=600)
        data = {
            'username': 'wrongotp',
            'email': 'wrongotp@example.com',
            'password': 'Password123!',
            'email_otp': '111111'
        }
        serializer = SignupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email_otp', serializer.errors)

    def test_signup_short_password(self):
        cache.set('signup_email_otp:shortpwd@example.com', '123456', timeout=600)
        data = {
            'username': 'shortpwd',
            'email': 'shortpwd@example.com',
            'password': 'short',
            'email_otp': '123456'
        }
        serializer = SignupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class LoginSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='ValidPassword123!'
        )

    def test_login_valid_credentials(self):
        serializer = LoginSerializer(data={'email': 'login@example.com', 'password': 'ValidPassword123!'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)

    def test_login_invalid_password(self):
        serializer = LoginSerializer(data={'email': 'login@example.com', 'password': 'WrongPassword!'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('credentials', serializer.errors)

    def test_login_inactive_account(self):
        self.user.is_active = False
        self.user.save()
        serializer = LoginSerializer(data={'email': 'login@example.com', 'password': 'ValidPassword123!'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('account', serializer.errors)


class ChangePasswordSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pwduser',
            email='pwd@example.com',
            password='OldPassword123!'
        )
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = self.user

    def test_change_password_success(self):
        serializer = ChangePasswordSerializer(
            data={
                'old_password': 'OldPassword123!',
                'new_password': 'BrandNewPassword123!',
                'confirm_password': 'BrandNewPassword123!'
            },
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(self.user.check_password('BrandNewPassword123!'))

    def test_change_password_wrong_old_password(self):
        serializer = ChangePasswordSerializer(
            data={
                'old_password': 'IncorrectOldPassword!',
                'new_password': 'BrandNewPassword123!',
                'confirm_password': 'BrandNewPassword123!'
            },
            context={'request': self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_change_password_mismatch(self):
        serializer = ChangePasswordSerializer(
            data={
                'old_password': 'OldPassword123!',
                'new_password': 'BrandNewPassword123!',
                'confirm_password': 'DifferentPassword123!'
            },
            context={'request': self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)


class SupportTicketSerializerTests(TestCase):
    def test_valid_ticket_serialization(self):
        serializer = SupportTicketSerializer(data={'subject': 'Billing error', 'message': 'I have a billing issue with booking #5.'})
        self.assertTrue(serializer.is_valid())

    def test_short_subject_rejected(self):
        serializer = SupportTicketSerializer(data={'subject': 'Hi', 'message': 'Valid message text here.'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('subject', serializer.errors)

    def test_short_message_rejected(self):
        serializer = SupportTicketSerializer(data={'subject': 'Valid Subject', 'message': 'Short'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)
