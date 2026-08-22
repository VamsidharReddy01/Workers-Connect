"""
Workers-Connect Locust Performance & Load Test Suite
Simulates concurrent user traffic (>= 300 concurrent simulated users) across all API endpoints.
"""

import os
import random
from locust import HttpUser, task, between, events


class WorkersConnectUser(HttpUser):
    wait_time = between(0.1, 0.5)
    host = os.getenv("TARGET_URL", "http://127.0.0.1:8000")

    def on_start(self):
        """Authenticate user or setup session headers."""
        self.access_token = None
        self.headers = {"Content-Type": "application/json"}
        # Attempt login with test user
        res = self.client.post(
            "/api/auth/login/",
            json={"email": "worker1@workersbridge.com", "password": "WorkerSecurePass123!"},
            headers=self.headers,
            name="Auth: Login"
        )
        if res.status_code == 200:
            data = res.json()
            self.access_token = data.get("access")
            self.headers["Authorization"] = f"Bearer {self.access_token}"

    # ── Browse & Search Tasks ─────────────────────────────────────────────────
    @task(5)
    def get_categories(self):
        self.client.get("/api/workers/categories/", headers=self.headers, name="Workers: Categories")

    @task(5)
    def get_job_categories(self):
        self.client.get("/api/workers/job-categories/", headers=self.headers, name="Workers: Job Categories")

    @task(8)
    def get_nearby_workers(self):
        lat = 17.385044 + random.uniform(-0.05, 0.05)
        lng = 78.486671 + random.uniform(-0.05, 0.05)
        self.client.get(f"/api/workers/nearby/?latitude={lat}&longitude={lng}", headers=self.headers, name="Workers: Nearby")

    @task(4)
    def get_worker_detail(self):
        worker_id = random.randint(1, 10)
        self.client.get(f"/api/workers/{worker_id}/", headers=self.headers, name="Workers: Detail View")

    # ── Authenticated User Flows ──────────────────────────────────────────────
    @task(6)
    def get_user_profile(self):
        self.client.get("/api/auth/profile/", headers=self.headers, name="Auth: Profile Detail")

    @task(4)
    def get_notifications(self):
        self.client.get("/api/notifications/", headers=self.headers, name="Notifications: List")

    @task(6)
    def get_unread_count(self):
        self.client.get("/api/notifications/unread-count/", headers=self.headers, name="Notifications: Unread Count")

    @task(4)
    def get_bookings(self):
        self.client.get("/api/workers/bookings/", headers=self.headers, name="Bookings: Worker List")

    @task(4)
    def get_my_bookings(self):
        self.client.get("/api/workers/bookings/my/", headers=self.headers, name="Bookings: Customer List")

    @task(3)
    def get_conversations(self):
        self.client.get("/api/workers/conversations/", headers=self.headers, name="Messages: Conversations List")

    @task(3)
    def get_support_tickets(self):
        self.client.get("/api/auth/support/tickets/", headers=self.headers, name="Support: Tickets List")
