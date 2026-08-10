from rest_framework import serializers
from .models import Booking, BookingReview, Conversation, JobCategory, Message, WorkerProfile, WorkerWorkImage
from accounts.serializers import UserSerializer, validate_latitude, validate_longitude


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'sort_order', 'is_active']


def _absolute_media_url(obj, request):
    if not obj:
        return None
    if request is not None:
        return request.build_absolute_uri(obj.url)
    return obj.url


class WorkerWorkImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkerWorkImage
        fields = ['id', 'image_url', 'caption', 'sort_order', 'created_at']

    def get_image_url(self, obj):
        if not obj.image:
            return None
        return _absolute_media_url(obj.image, self.context.get('request'))


class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    work_images = WorkerWorkImageSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = [
            'id',
            'user',
            'category',
            'price',
            'bio',
            'is_online',
            'rating',
            'total_reviews',
            'experience_years',
            'cover_image_url',
            'work_images',
        ]

    def get_cover_image_url(self, obj):
        first_image = obj.work_images.first()
        if not first_image or not first_image.image:
            return None
        return _absolute_media_url(first_image.image, self.context.get('request'))


class WorkerProfileCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, source='user.username')
    phone_number = serializers.CharField(required=False, allow_blank=True, source='user.phone_number')
    address = serializers.CharField(required=False, allow_blank=True, source='user.location')
    skills = serializers.CharField(required=False, source='category')
    description = serializers.CharField(required=False, allow_blank=True, source='bio')
    availability = serializers.BooleanField(required=False, source='is_online')
    profile_photo = serializers.ImageField(required=False, source='user.profile_photo')

    class Meta:
        model = WorkerProfile
        fields = [
            'category',
            'skills',
            'price',
            'experience_years',
            'is_online',
            'availability',
            'bio',
            'description',
            'username',
            'phone_number',
            'address',
            'profile_photo',
        ]

    def validate_category(self, value):
        value = value.strip().title()
        if len(value) < 2:
            raise serializers.ValidationError('Category must be at least 2 characters.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError('Experience years cannot be negative.')
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return instance


class BookingSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    worker = WorkerProfileSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_review = serializers.SerializerMethodField()
    conversation_id = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'customer',
            'worker',
            'service_category',
            'description',
            'address',
            'service_latitude',
            'service_longitude',
            'location_permission_granted',
            'scheduled_at',
            'total_amount',
            'status',
            'status_display',
            'has_review',
            'conversation_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_has_review(self, obj):
        try:
            obj.review
            return True
        except BookingReview.DoesNotExist:
            return False

    def get_conversation_id(self, obj):
        if hasattr(obj, 'conversation') and obj.conversation:
            return obj.conversation.id
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    worker_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            'worker_id',
            'service_category',
            'description',
            'address',
            'service_latitude',
            'service_longitude',
            'location_permission_granted',
            'scheduled_at',
            'total_amount',
        ]

    def validate_worker_id(self, value):
        if not WorkerProfile.objects.filter(id=value, is_online=True).exists():
            raise serializers.ValidationError('Selected worker is not available.')
        return value

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Total amount must be greater than zero.')
        return value

    def validate_service_latitude(self, value):
        return validate_latitude(value)

    def validate_service_longitude(self, value):
        return validate_longitude(value)

    def validate(self, attrs):
        latitude = attrs.get('service_latitude')
        longitude = attrs.get('service_longitude')
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                {'location': 'Service latitude and longitude must be provided together.'}
            )
        return attrs

    def create(self, validated_data):
        worker_id = validated_data.pop('worker_id')
        booking = Booking.objects.create(
            customer=self.context['request'].user,
            worker_id=worker_id,
            **validated_data,
        )
        conversation = Conversation.objects.create(
            booking=booking,
            customer=booking.customer,
            worker=booking.worker,
        )
        Message.objects.create(
            conversation=conversation,
            sender=booking.customer,
            text=(
                f'Hi! I booked your {booking.service_category} service. '
                f'Looking forward to working with you.'
            ),
        )
        return booking


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'created_at', 'is_read']


class ConversationSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_party_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'booking',
            'last_message',
            'unread_count',
            'other_party_name',
            'created_at',
            'updated_at',
        ]

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if not last:
            return None
        return MessageSerializer(last).data

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()

    def get_other_party_name(self, obj):
        request = self.context.get('request')
        if not request:
            return ''
        if request.user.id == obj.customer_id:
            return obj.worker.user.username.replace('_', ' ')
        return obj.customer.username.replace('_', ' ')


class BookingReviewSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)

    class Meta:
        model = BookingReview
        fields = ['id', 'booking', 'customer', 'worker', 'rating', 'feedback', 'created_at']
        read_only_fields = ['id', 'customer', 'worker', 'created_at']


class BookingReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class BookingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            Booking.STATUS_ACCEPTED,
            Booking.STATUS_DECLINED,
            Booking.STATUS_ON_THE_WAY,
            Booking.STATUS_IN_PROGRESS,
            Booking.STATUS_COMPLETED,
            Booking.STATUS_CANCELLED,
        ]
    )

    _allowed_transitions = {
        Booking.STATUS_REQUESTED: {
            Booking.STATUS_ACCEPTED,
            Booking.STATUS_DECLINED,
            Booking.STATUS_CANCELLED,
        },
        Booking.STATUS_ACCEPTED: {
            Booking.STATUS_ON_THE_WAY,
            Booking.STATUS_IN_PROGRESS,
            Booking.STATUS_CANCELLED,
        },
        Booking.STATUS_ON_THE_WAY: {
            Booking.STATUS_IN_PROGRESS,
            Booking.STATUS_COMPLETED,
            Booking.STATUS_CANCELLED,
        },
        Booking.STATUS_IN_PROGRESS: {
            Booking.STATUS_COMPLETED,
            Booking.STATUS_CANCELLED,
        },
    }

    def validate_status(self, value):
        booking = self.context['booking']
        allowed = self._allowed_transitions.get(booking.status, set())
        if value not in allowed:
            raise serializers.ValidationError(
                f'Cannot change booking from {booking.status} to {value}.'
            )
        return value
