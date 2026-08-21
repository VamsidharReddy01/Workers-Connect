from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, SupportTicket
from accounts.serializers import (
    UserSerializer,
    SupportTicketSerializer,
    MAX_PROFILE_PHOTO_SIZE,
    ALLOWED_IMAGE_TYPES,
)
from accounts.tests.test_serializers import create_dummy_image


class SerializerFieldsAndMethodsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='field_user',
            email='fu@example.com',
            password='Password123!',
            role='customer',
            phone_number='1234567890'
        )

    def test_phone_number_empty_string_allowed(self):
        serializer = UserSerializer(instance=self.user, data={'phone_number': ''}, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_phone_number_none_allowed(self):
        serializer = UserSerializer(instance=self.user, data={'phone_number': None}, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_profile_photo_size_exceeded_rejected(self):
        # Create a dummy payload larger than 5MB
        big_content = b'x' * (MAX_PROFILE_PHOTO_SIZE + 1024)
        big_file = SimpleUploadedFile("big.jpg", big_content, content_type="image/jpeg")
        serializer = UserSerializer(instance=self.user, data={'profile_photo': big_file}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile_photo', serializer.errors)

    def test_profile_photo_valid_upload_and_url(self):
        img_file = create_dummy_image('JPEG')
        serializer = UserSerializer(instance=self.user, data={'profile_photo': img_file}, partial=True)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertTrue(bool(updated.profile_photo))
        data = UserSerializer(updated).data
        self.assertIsNotNone(data['profile_photo_url'])

    def test_support_ticket_status_display_field(self):
        t = SupportTicket.objects.create(user=self.user, subject='Help needed', message='Message content here.', status='in_progress')
        serializer = SupportTicketSerializer(t)
        self.assertEqual(serializer.data['status_display'], 'In Progress')
