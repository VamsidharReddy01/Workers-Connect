from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User


class EmailBackend(ModelBackend):
    """
    Authenticate using either email address (case-insensitive) or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
        if not username or not password:
            return None

        try:
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password):
            return user

        return None
