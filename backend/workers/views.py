import math
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count, Min, Q, Sum
from django.db.models.functions import Lower
from .models import (
    Booking,
    BookingReview,
    Conversation,
    JobCategory,
    Message,
    WorkerProfile,
    WorkerWorkImage,
)
from .serializers import (
    BookingCreateSerializer,
    BookingReviewCreateSerializer,
    BookingReviewSerializer,
    BookingSerializer,
    BookingStatusUpdateSerializer,
    ConversationSerializer,
    MessageSerializer,
    PublicWorkerProfileSerializer,
    WorkerProfileCreateSerializer,
    WorkerProfileSerializer,
    WorkerWorkImageSerializer,
)
from accounts.serializers import _validate_image_magic_bytes

import logging

logger = logging.getLogger(__name__)

ALLOWED_USER_UPDATE_FIELDS = {'username', 'phone_number', 'location', 'profile_photo'}


def _notify_status_change(booking, new_status):
    """Call the appropriate NotificationService helper for a job status change.
    Wrapped in try/except — notification failure must NOT block the status update."""
    try:
        from notifications.services import NotificationService
        handlers = {
            Booking.STATUS_ACCEPTED: NotificationService.notify_job_accepted,
            Booking.STATUS_DECLINED: NotificationService.notify_job_declined,
            Booking.STATUS_ON_THE_WAY: NotificationService.notify_worker_on_the_way,
            Booking.STATUS_IN_PROGRESS: NotificationService.notify_job_started,
            Booking.STATUS_COMPLETED: NotificationService.notify_job_completed,
        }
        handler = handlers.get(new_status)
        if handler:
            handler(booking)
        elif new_status == Booking.STATUS_CANCELLED:
            cancelled_by = 'worker'
            NotificationService.notify_job_cancelled(booking, cancelled_by=cancelled_by)
    except Exception as exc:
        logger.error('Notification error after status change to %s for booking #%s: %s',
                     new_status, booking.id, exc)

MAX_PORTFOLIO_IMAGES = 8
MAX_WORK_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_WORK_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}

DEFAULT_JOB_CATEGORIES = [
    'Electrician',
    'Plumber',
    'Carpenter',
    'Painter',
    'House Cleaner',
    'AC Repair',
    'Mason',
    'Welder',
    'Gardener',
    'Pest Control',
]


def _ensure_job_categories():
    """Seed predefined categories if the table is empty (e.g. before migrations run)."""
    if JobCategory.objects.exists():
        return
    JobCategory.objects.bulk_create(
        [
            JobCategory(name=name, sort_order=index)
            for index, name in enumerate(DEFAULT_JOB_CATEGORIES)
        ],
        ignore_conflicts=True,
    )


def _category_list_payload():
    return list(
        WorkerProfile.objects.filter(user__role='worker')
        .exclude(category__isnull=True)
        .exclude(category__exact='')
        .annotate(category_key=Lower('category'))
        .values('category_key')
        .annotate(
            category=Min('category'),
            worker_count=Count('id'),
            online_worker_count=Count('id', filter=Q(is_online=True)),
        )
        .order_by('-worker_count', 'category')
        .values('category', 'worker_count', 'online_worker_count')
    )


def _recalculate_worker_rating(worker_profile):
    stats = BookingReview.objects.filter(worker=worker_profile).aggregate(
        avg_rating=Avg('rating'),
        total=Count('id'),
    )
    worker_profile.rating = round(stats['avg_rating'] or 4.8, 1)
    worker_profile.total_reviews = stats['total'] or 0
    worker_profile.save(update_fields=['rating', 'total_reviews'])


def _user_conversations(user):
    if getattr(user, 'role', None) == 'worker':
        try:
            profile = user.worker_profile
        except WorkerProfile.DoesNotExist:
            return Conversation.objects.none()
        return Conversation.objects.filter(worker=profile)
    return Conversation.objects.filter(customer=user)


def _user_can_access_conversation(user, conversation):
    if getattr(user, 'role', None) == 'worker':
        try:
            return conversation.worker.user_id == user.id
        except WorkerProfile.DoesNotExist:
            return False
    return conversation.customer_id == user.id


def _require_worker_profile(user):
    try:
        return user.worker_profile, None
    except WorkerProfile.DoesNotExist:
        return None, Response(
            {"error": "Worker profile not created yet"},
            status=status.HTTP_404_NOT_FOUND,
        )


class WorkerProfileDetailView(APIView):
    """
    API View to retrieve and create/update the worker's own profile (specialty/category, price).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        try:
            profile = (
                WorkerProfile.objects.select_related('user')
                .prefetch_related('work_images')
                .get(user=request.user)
            )
            return Response(
                WorkerProfileSerializer(profile, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        except WorkerProfile.DoesNotExist:
            return Response({"error": "Profile not created yet"}, status=status.HTTP_404_NOT_FOUND)
            
    def post(self, request):
        # Create or update profile
        serializer = WorkerProfileCreateSerializer(data=request.data)
        if serializer.is_valid():
            if getattr(request.user, 'role', None) != 'worker':
                return Response(
                    {"error": "Only worker accounts can create worker profiles."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            profile, created = WorkerProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    'category': serializer.validated_data['category'],
                    'price': serializer.validated_data['price'],
                    'experience_years': serializer.validated_data.get('experience_years', 1),
                    'is_online': serializer.validated_data.get('is_online', True),
                    'bio': serializer.validated_data.get('bio', ''),
                }
            )
            # SECURITY FIX #13: Explicit whitelist for user updates (protect against mass assignment)
            user_data = serializer.validated_data.get('user', {})
            if user_data:
                for attr, value in user_data.items():
                    if attr in ALLOWED_USER_UPDATE_FIELDS:
                        setattr(request.user, attr, value)
                request.user.save()
            profile = (
                WorkerProfile.objects.select_related('user')
                .prefetch_related('work_images')
                .get(pk=profile.pk)
            )
            return Response(
                WorkerProfileSerializer(profile, context={'request': request}).data,
                status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        serializer = WorkerProfileCreateSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
            profile = (
                WorkerProfile.objects.select_related('user')
                .prefetch_related('work_images')
                .get(pk=profile.pk)
            )
            return Response(
                WorkerProfileSerializer(profile, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class WorkerAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        is_online_raw = request.data.get('is_online')
        if isinstance(is_online_raw, bool):
            is_online = is_online_raw
        elif isinstance(is_online_raw, str) and is_online_raw.lower() in ('true', 'false', '1', '0'):
            is_online = is_online_raw.lower() in ('true', '1')
        elif isinstance(is_online_raw, int) and is_online_raw in (0, 1):
            is_online = bool(is_online_raw)
        else:
            return Response(
                {"errors": {"is_online": ["This field must be true or false."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.is_online = is_online
        profile.save(update_fields=['is_online'])
        profile = (
            WorkerProfile.objects.select_related('user')
            .prefetch_related('work_images')
            .get(pk=profile.pk)
        )
        return Response(
            WorkerProfileSerializer(profile, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class WorkerDashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        bookings = Booking.objects.filter(worker=profile)
        earnings = bookings.filter(status=Booking.STATUS_COMPLETED).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        return Response(
            {
                "profile": WorkerProfileSerializer(
                    profile,
                    context={'request': request},
                ).data,
                "metrics": {
                    "pending_requests": bookings.filter(status=Booking.STATUS_REQUESTED).count(),
                    "active_jobs": bookings.filter(
                        status__in=[
                            Booking.STATUS_ACCEPTED,
                            Booking.STATUS_ON_THE_WAY,
                            Booking.STATUS_IN_PROGRESS,
                        ]
                    ).count(),
                    "completed_jobs": bookings.filter(status=Booking.STATUS_COMPLETED).count(),
                    "total_earnings": str(earnings),
                },
            },
            status=status.HTTP_200_OK,
        )


class WorkerBookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        queryset = Booking.objects.filter(worker=profile).select_related(
            'customer', 'worker__user', 'conversation', 'review'
        )
        booking_status = request.query_params.get('status')
        if booking_status:
            queryset = queryset.filter(status=booking_status)

        serializer = BookingSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)


class WorkerBookingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, booking_id):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        try:
            booking = Booking.objects.select_related('customer', 'worker__user').get(
                id=booking_id,
                worker=profile,
            )
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookingStatusUpdateSerializer(
            data=request.data,
            context={"booking": booking},
        )
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            # Only fire notification if status actually changes
            status_changed = booking.status != new_status
            booking.status = new_status
            booking.save(update_fields=['status', 'updated_at'])
            booking = Booking.objects.select_related(
                'customer', 'worker__user', 'conversation', 'review'
            ).prefetch_related('worker__work_images').get(pk=booking.pk)
            if status_changed:
                _notify_status_change(booking, new_status)
            return Response(
                BookingSerializer(booking, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CustomerBookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if getattr(request.user, 'role', None) != 'customer':
            return Response(
                {"error": "Only customer accounts can create bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            booking = serializer.save()
            booking = Booking.objects.select_related(
                'customer', 'worker__user', 'conversation', 'review'
            ).prefetch_related('worker__work_images').get(pk=booking.pk)
            # Notify the worker of the new job request
            try:
                from notifications.services import NotificationService
                NotificationService.notify_new_job_request(booking)
            except Exception as exc:
                logger.error('Failed to notify worker of new booking #%s: %s', booking.id, exc)
            return Response(
                BookingSerializer(booking, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CustomerBookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) != 'customer':
            return Response(
                {"error": "Only customer accounts can view customer bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = (
            Booking.objects.filter(customer=request.user)
            .select_related('customer', 'worker__user', 'conversation', 'review')
            .prefetch_related('worker__work_images')
            .order_by('-created_at')
        )
        booking_status = request.query_params.get('status')
        if booking_status:
            queryset = queryset.filter(status=booking_status)

        serializer = BookingSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)


# SECURITY FIX #17: Customer cancellation endpoint with appropriate business logic
class CustomerBookingCancelView(APIView):
    """
    API View to allow customers to cancel their own booking before completion.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, booking_id):
        if getattr(request.user, 'role', None) != 'customer':
            return Response(
                {"error": "Only customer accounts can cancel customer bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.select_related('customer', 'worker__user').get(
                id=booking_id,
                customer=request.user,
            )
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        if booking.status in (Booking.STATUS_COMPLETED, Booking.STATUS_DECLINED, Booking.STATUS_CANCELLED):
            return Response(
                {"error": f"Cannot cancel a booking that is already {booking.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        booking = Booking.objects.select_related(
            'customer', 'worker__user', 'conversation', 'review'
        ).prefetch_related('worker__work_images').get(pk=booking.pk)

        # Notify worker that the booking was cancelled by the customer
        try:
            from notifications.services import NotificationService
            NotificationService.notify_job_cancelled(booking, cancelled_by='customer')
        except Exception as exc:
            logger.error('Failed to notify worker of customer-cancelled booking #%s: %s', booking.id, exc)

        return Response(
            BookingSerializer(booking, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, booking_id):
        return self.patch(request, booking_id)



class BookingReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if getattr(request.user, 'role', None) != 'customer':
            return Response(
                {"error": "Only customers can submit reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.select_related('worker', 'review').get(
                id=booking_id,
                customer=request.user,
            )
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != Booking.STATUS_COMPLETED:
            return Response(
                {"error": "You can review only after the work is completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(booking, 'review') and booking.review:
            return Response(
                {"error": "You have already reviewed this booking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BookingReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        review = BookingReview.objects.create(
            booking=booking,
            customer=request.user,
            worker=booking.worker,
            rating=serializer.validated_data['rating'],
            feedback=serializer.validated_data.get('feedback', ''),
        )
        _recalculate_worker_rating(booking.worker)
        return Response(
            BookingReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            _user_conversations(request.user)
            .select_related('booking', 'customer', 'worker__user')
            .prefetch_related('messages')
            .order_by('-updated_at')
        )
        serializer = ConversationSerializer(
            conversations,
            many=True,
            context={'request': request},
        )
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)


class ConversationMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        if not _user_can_access_conversation(request.user, conversation):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        conversation.messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True)

        messages = conversation.messages.select_related('sender').order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        if not _user_can_access_conversation(request.user, conversation):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        text = (request.data.get('text') or '').strip()
        if not text:
            return Response(
                {"errors": {"text": ["Message cannot be empty."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=text,
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        # Notify the other party of the new message
        try:
            from notifications.services import NotificationService
            conversation_with_related = Conversation.objects.select_related(
                'customer', 'worker__user', 'booking'
            ).get(pk=conversation.pk)
            NotificationService.notify_new_message(message, conversation_with_related)
        except Exception as exc:
            logger.error('Failed to send message notification for conversation #%s: %s',
                         conversation.id, exc)

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class CategoryListView(APIView):
    """
    Lists popular categories for customer browse, derived from registered
    worker profiles and ordered by the number of registrations.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'list': _category_list_payload()}, status=status.HTTP_200_OK)


class JobCategoryOptionsView(APIView):
    """Simple category name list for dropdowns (worker job profile setup)."""
    permission_classes = [AllowAny]

    def get(self, request):
        _ensure_job_categories()
        names = list(
            JobCategory.objects.filter(is_active=True)
            .order_by('sort_order', 'name')
            .values_list('name', flat=True)
        )
        return Response({'list': names}, status=status.HTTP_200_OK)


def _haversine_km(lat1, lon1, lat2, lon2):
    try:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
        r = 6371.0
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(float(lat1)))
            * math.cos(math.radians(float(lat2)))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)
    except (ValueError, TypeError):
        return None


class NearbyWorkersView(APIView):
    """
    API View to list registered workers with geographic distance calculation.
    Uses PublicWorkerProfileSerializer to avoid leaking sensitive user information.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = (
            WorkerProfile.objects.select_related('user')
            .prefetch_related('work_images')
            .filter(user__role='worker')
            .exclude(category__isnull=True)
            .exclude(category__exact='')
        )
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        available_only = request.query_params.get('available_only')

        user_lat = request.query_params.get('lat') or request.query_params.get('latitude')
        user_lng = request.query_params.get('lng') or request.query_params.get('longitude')
        if user_lat is None and request.user.is_authenticated and getattr(request.user, 'latitude', None) is not None:
            user_lat = request.user.latitude
            user_lng = request.user.longitude

        if user_lat is not None or user_lng is not None:
            try:
                user_lat = float(user_lat)
                user_lng = float(user_lng)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid latitude or longitude coordinates.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not (-90 <= user_lat <= 90) or not (-180 <= user_lng <= 180):
                return Response(
                    {'error': 'Coordinates out of range.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        radius_param = request.query_params.get('radius')
        radius = None
        if radius_param is not None:
            try:
                radius = float(radius_param)
                if radius <= 0 or radius > 1000:
                    return Response(
                        {'error': 'Radius must be a positive number up to 1000 km.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid radius parameter.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if category:
            queryset = queryset.filter(category__iexact=category)
        if available_only and available_only.lower() in {'1', 'true', 'yes'}:
            queryset = queryset.filter(is_online=True)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(category__icontains=search) |
                Q(user__location__icontains=search)
            )

        distances = {}
        if user_lat is not None and user_lng is not None:
            filtered_profiles = []
            for profile in queryset:
                w_lat = profile.user.latitude
                w_lng = profile.user.longitude
                dist = _haversine_km(user_lat, user_lng, w_lat, w_lng)
                distances[profile.id] = dist

                if radius is not None:
                    if dist is not None and dist <= radius:
                        filtered_profiles.append(profile)
                else:
                    filtered_profiles.append(profile)
            target_list = filtered_profiles
        else:
            target_list = list(queryset)

        serializer = PublicWorkerProfileSerializer(
            target_list,
            many=True,
            context={'request': request, 'distances': distances},
        )
        data = serializer.data

        if user_lat is not None and user_lng is not None:
            data.sort(
                key=lambda x: (
                    not x.get('is_online', False),
                    x.get('distance_km') if x.get('distance_km') is not None else 999999,
                )
            )

        return Response({'list': data, 'results': data, 'count': len(data)}, status=status.HTTP_200_OK)


class WorkerPublicDetailView(APIView):
    """Public worker profile with portfolio images for customer detail screen."""
    permission_classes = [AllowAny]

    def get(self, request, worker_id):
        try:
            profile = (
                WorkerProfile.objects.select_related('user')
                .prefetch_related('work_images')
                .get(id=worker_id, user__role='worker')
            )
        except WorkerProfile.DoesNotExist:
            return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

        distances = {}
        user_lat = request.query_params.get('lat') or request.query_params.get('latitude')
        user_lng = request.query_params.get('lng') or request.query_params.get('longitude')
        if user_lat is None and request.user.is_authenticated and getattr(request.user, 'latitude', None) is not None:
            user_lat = request.user.latitude
            user_lng = request.user.longitude

        if user_lat is not None and user_lng is not None and profile.user.latitude is not None and profile.user.longitude is not None:
            distances[profile.id] = _haversine_km(user_lat, user_lng, profile.user.latitude, profile.user.longitude)

        return Response(
            PublicWorkerProfileSerializer(profile, context={'request': request, 'distances': distances}).data,
            status=status.HTTP_200_OK,
        )


class WorkerWorkImageView(APIView):
    """List, upload, or delete portfolio images for the authenticated worker."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        images = profile.work_images.all()
        serializer = WorkerWorkImageSerializer(
            images,
            many=True,
            context={'request': request},
        )
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        uploads = request.FILES.getlist('images')
        if not uploads and request.FILES.get('image'):
            uploads = [request.FILES['image']]
        if not uploads:
            return Response(
                {'error': 'No images uploaded. Send files as "images".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_count = profile.work_images.count()
        if existing_count + len(uploads) > MAX_PORTFOLIO_IMAGES:
            return Response(
                {
                    'error': f'You can upload up to {MAX_PORTFOLIO_IMAGES} portfolio images.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # SECURITY FIX #16: Validate size, Content-Type AND Pillow magic bytes
        for upload in uploads:
            if upload.size > MAX_WORK_IMAGE_SIZE:
                return Response(
                    {'errors': {'images': ['Each image must be 5 MB or smaller.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if getattr(upload, 'content_type', '') not in ALLOWED_WORK_IMAGE_TYPES:
                return Response(
                    {'errors': {'images': ['Upload JPG, PNG, or WebP images only.']}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                _validate_image_magic_bytes(upload)
            except Exception as e:
                return Response(
                    {'errors': {'images': [str(e)]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        caption = request.data.get('caption', '')
        created = []
        next_order = existing_count
        for upload in uploads:
            image = WorkerWorkImage.objects.create(
                worker=profile,
                image=upload,
                caption=caption,
                sort_order=next_order,
            )
            next_order += 1
            created.append(image)

        serializer = WorkerWorkImageSerializer(
            created,
            many=True,
            context={'request': request},
        )
        return Response({'list': serializer.data}, status=status.HTTP_201_CREATED)


class WorkerWorkImageDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, image_id):
        profile, error = _require_worker_profile(request.user)
        if error:
            return error

        try:
            image = profile.work_images.get(id=image_id)
        except WorkerWorkImage.DoesNotExist:
            return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)

        image.image.delete(save=False)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
