from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from workers.models import Booking, WorkerProfile
from workers.serializers import BookingStatusUpdateSerializer


class BookingStatusFlowDeepTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='flow_cust_u', email='fcu@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='flow_work_u', email='fwu@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Plumber', price=40.00)

    def _create_booking(self, status):
        return Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Address',
            scheduled_at=timezone.now(),
            total_amount=80.00,
            status=status
        )

    # ── REQUESTED Status Transitions ──────────────────────────────────────────
    def test_from_requested_to_accepted_valid(self):
        b = self._create_booking(Booking.STATUS_REQUESTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_ACCEPTED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_requested_to_declined_valid(self):
        b = self._create_booking(Booking.STATUS_REQUESTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_DECLINED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_requested_to_cancelled_valid(self):
        b = self._create_booking(Booking.STATUS_REQUESTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_CANCELLED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_requested_to_in_progress_invalid(self):
        b = self._create_booking(Booking.STATUS_REQUESTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_IN_PROGRESS}, context={'booking': b})
        self.assertFalse(s.is_valid())

    def test_from_requested_to_completed_invalid(self):
        b = self._create_booking(Booking.STATUS_REQUESTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_COMPLETED}, context={'booking': b})
        self.assertFalse(s.is_valid())

    # ── ACCEPTED Status Transitions ───────────────────────────────────────────
    def test_from_accepted_to_on_the_way_valid(self):
        b = self._create_booking(Booking.STATUS_ACCEPTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_ON_THE_WAY}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_accepted_to_cancelled_valid(self):
        b = self._create_booking(Booking.STATUS_ACCEPTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_CANCELLED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_accepted_to_completed_invalid(self):
        b = self._create_booking(Booking.STATUS_ACCEPTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_COMPLETED}, context={'booking': b})
        self.assertFalse(s.is_valid())

    def test_from_accepted_to_declined_invalid(self):
        b = self._create_booking(Booking.STATUS_ACCEPTED)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_DECLINED}, context={'booking': b})
        self.assertFalse(s.is_valid())

    # ── ON_THE_WAY Status Transitions ─────────────────────────────────────────
    def test_from_on_the_way_to_in_progress_valid(self):
        b = self._create_booking(Booking.STATUS_ON_THE_WAY)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_IN_PROGRESS}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_on_the_way_to_cancelled_valid(self):
        b = self._create_booking(Booking.STATUS_ON_THE_WAY)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_CANCELLED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_on_the_way_to_completed_invalid(self):
        b = self._create_booking(Booking.STATUS_ON_THE_WAY)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_COMPLETED}, context={'booking': b})
        self.assertFalse(s.is_valid())

    # ── IN_PROGRESS Status Transitions ────────────────────────────────────────
    def test_from_in_progress_to_completed_valid(self):
        b = self._create_booking(Booking.STATUS_IN_PROGRESS)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_COMPLETED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_in_progress_to_cancelled_valid(self):
        b = self._create_booking(Booking.STATUS_IN_PROGRESS)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_CANCELLED}, context={'booking': b})
        self.assertTrue(s.is_valid())

    def test_from_in_progress_to_accepted_invalid(self):
        b = self._create_booking(Booking.STATUS_IN_PROGRESS)
        s = BookingStatusUpdateSerializer(data={'status': Booking.STATUS_ACCEPTED}, context={'booking': b})
        self.assertFalse(s.is_valid())

    # ── COMPLETED / DECLINED / CANCELLED (Terminal States) ────────────────────
    def test_from_completed_to_any_invalid(self):
        b = self._create_booking(Booking.STATUS_COMPLETED)
        for target in [Booking.STATUS_REQUESTED, Booking.STATUS_ACCEPTED, Booking.STATUS_CANCELLED]:
            s = BookingStatusUpdateSerializer(data={'status': target}, context={'booking': b})
            self.assertFalse(s.is_valid())

    def test_from_cancelled_to_any_invalid(self):
        b = self._create_booking(Booking.STATUS_CANCELLED)
        for target in [Booking.STATUS_REQUESTED, Booking.STATUS_ACCEPTED, Booking.STATUS_IN_PROGRESS]:
            s = BookingStatusUpdateSerializer(data={'status': target}, context={'booking': b})
            self.assertFalse(s.is_valid())
