from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from workers.models import (
    JobCategory,
    WorkerProfile,
    WorkerWorkImage,
    Booking,
    Conversation,
    Message,
    BookingReview,
)


class JobCategoryModelTests(TestCase):
    def setUp(self):
        JobCategory.objects.all().delete()

    def test_create_job_category(self):
        cat = JobCategory.objects.create(name='TestElectrician', sort_order=1, is_active=True)
        self.assertEqual(cat.name, 'TestElectrician')
        self.assertEqual(cat.sort_order, 1)
        self.assertTrue(cat.is_active)
        self.assertEqual(str(cat), 'TestElectrician')

    def test_job_category_ordering(self):
        c2 = JobCategory.objects.create(name='TestPlumber', sort_order=2)
        c1 = JobCategory.objects.create(name='TestCarpenter', sort_order=1)
        cats = list(JobCategory.objects.all())
        self.assertEqual(cats[0].name, 'TestCarpenter')
        self.assertEqual(cats[1].name, 'TestPlumber')


class WorkerProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='worker1',
            email='w1@example.com',
            password='Password123!',
            role='worker'
        )

    def test_create_worker_profile_defaults(self):
        profile = WorkerProfile.objects.create(
            user=self.user,
            category='Plumber',
            price=45.50
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.category, 'Plumber')
        self.assertEqual(float(profile.price), 45.50)
        self.assertEqual(profile.bio, '')
        self.assertTrue(profile.is_online)
        self.assertEqual(profile.rating, 4.8)
        self.assertEqual(profile.total_reviews, 120)
        self.assertEqual(profile.experience_years, 1)
        self.assertIn('worker1 - Plumber ($45.5/hr)', str(profile))


class WorkerWorkImageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='imgworker', email='iw@example.com', password='pwd', role='worker')
        self.profile = WorkerProfile.objects.create(user=self.user, category='Painter', price=30.00)

    def test_create_work_image(self):
        img = WorkerWorkImage.objects.create(
            worker=self.profile,
            image='worker_portfolio/test.jpg',
            caption='Living Room Wall Painting',
            sort_order=0
        )
        self.assertEqual(img.worker, self.profile)
        self.assertEqual(img.caption, 'Living Room Wall Painting')
        self.assertIn('imgworker portfolio', str(img))


class BookingModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='customer1', email='c1@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='worker2', email='w2@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Electrician', price=60.00)

    def test_create_booking_defaults(self):
        booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Electrician',
            description='Fix breaker switch',
            address='456 Oak Avenue',
            service_latitude=17.44,
            service_longitude=78.38,
            scheduled_at=timezone.now(),
            total_amount=120.00
        )
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.worker, self.worker_profile)
        self.assertEqual(booking.status, Booking.STATUS_REQUESTED)
        self.assertIn('Electrician - worker2', str(booking))

    def test_booking_status_choices(self):
        for status_val, label in Booking.STATUS_CHOICES:
            b = Booking.objects.create(
                customer=self.customer,
                worker=self.worker_profile,
                service_category='Electrician',
                address='Test Address',
                scheduled_at=timezone.now(),
                total_amount=50.00,
                status=status_val
            )
            self.assertEqual(b.status, status_val)


class ConversationAndMessageModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='chat_cust', email='cc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='chat_work', email='cw@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Cleaner', price=25.00)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Cleaner',
            address='Home Address',
            scheduled_at=timezone.now(),
            total_amount=50.00
        )

    def test_create_conversation(self):
        conv = Conversation.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile
        )
        self.assertEqual(conv.booking, self.booking)
        self.assertIn(f"Chat #{conv.id}", str(conv))

    def test_create_message(self):
        conv = Conversation.objects.create(booking=self.booking, customer=self.customer, worker=self.worker_profile)
        msg = Message.objects.create(
            conversation=conv,
            sender=self.customer,
            text='Hello, are you available today?',
            is_read=False
        )
        self.assertEqual(msg.conversation, conv)
        self.assertEqual(msg.sender, self.customer)
        self.assertFalse(msg.is_read)
        self.assertIn(f"Message #{msg.id}", str(msg))


class BookingReviewModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='rev_cust', email='rc@example.com', password='pwd', role='customer')
        self.worker_user = User.objects.create_user(username='rev_work', email='rw@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Plumber', price=40.00)
        self.booking = Booking.objects.create(
            customer=self.customer,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Street 1',
            scheduled_at=timezone.now(),
            total_amount=80.00,
            status=Booking.STATUS_COMPLETED
        )

    def test_create_review(self):
        review = BookingReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            worker=self.worker_profile,
            rating=5,
            feedback='Excellent plumbing work!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.feedback, 'Excellent plumbing work!')
        self.assertIn("Review 5/5", str(review))
