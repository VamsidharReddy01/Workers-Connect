from django.test import TestCase
from django.conf import settings
from config.settings import env_bool, env_list


class ConfigEnvironmentHelpersTests(TestCase):
    def test_env_bool_true_values(self):
        import os
        for val in ['1', 'true', 'True', 'YES', 'yes', 'on', 'ON']:
            os.environ['TEST_BOOL'] = val
            self.assertTrue(env_bool('TEST_BOOL'))

    def test_env_bool_false_values(self):
        import os
        for val in ['0', 'false', 'False', 'NO', 'no', 'off', 'random']:
            os.environ['TEST_BOOL'] = val
            self.assertFalse(env_bool('TEST_BOOL'))

    def test_env_list_parsing(self):
        import os
        os.environ['TEST_LIST'] = '  http://localhost:5173, http://127.0.0.1:3000 , https://app.example.com  '
        parsed = env_list('TEST_LIST')
        self.assertEqual(parsed, ['http://localhost:5173', 'http://127.0.0.1:3000', 'https://app.example.com'])

    def test_env_list_empty(self):
        import os
        os.environ['TEST_EMPTY_LIST'] = ' , , '
        parsed = env_list('TEST_EMPTY_LIST')
        self.assertEqual(parsed, [])

    def test_settings_security_configurations(self):
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertIn('rest_framework_simplejwt.authentication.JWTAuthentication', settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'])
        self.assertTrue(settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'])
        self.assertTrue(settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'])
