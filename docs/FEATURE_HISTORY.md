# WorkersBridge - Feature History

## [Feature] Worker vs Customer Signup UI Differentiated & API Role Provisioning
- **Date**: August 2026
- **Status**: Completed & Verified
- **Scope**:
  - **Backend**:
    - Updated `SignupSerializer` to support `role='worker'` and `role='customer'`, rejecting invalid/admin roles with 400 Bad Request.
    - Added automatic `WorkerProfile` generation with chosen category on worker registration.
    - Added dedicated endpoints `POST /api/auth/worker-signup/` (alias `POST /api/auth/signup/worker/`) and `POST /api/auth/customer-signup/` (alias `POST /api/auth/signup/customer/`).
    - Added 4 unit/integration tests in `backend/accounts/tests/test_signup_roles.py`.
  - **Web Frontend**:
    - Added **"Wanna Join as Worker?"** callout card, pro worker badge, trade/category dropdown selector, and distinct emerald/green button styles on worker registration.
    - Added "Wanna Join as Worker?" switch banner on customer signup.
    - Routed `api.signup()` to `/api/auth/worker-signup/` when `role === 'worker'` and `/api/auth/customer-signup/` when `role === 'customer'`.
  - **Mobile Frontend**:
    - Added distinct Worker vs Customer signup cards, pro worker badge, category input, and "Wanna Join as Worker?" banner in React Native/Expo auth screen.
    - Routed mobile `api.signup()` to dedicated worker/customer endpoints.

---

## [Feature] Nearby Workers with Distance Calculation & Radius Filtering
- **Date**: August 2026
- **Status**: Completed & Verified
- **Scope**:
  - **Backend**:
    - Added `name`, `latitude`, `longitude`, `location_name`, and `distance_km` fields to `PublicWorkerProfileSerializer` and `WorkerProfileSerializer`.
    - Added database index on `User(latitude, longitude)` for spatial query optimization.
    - Updated `NearbyWorkersView` (`GET /api/workers/nearby/` and `GET /api/workers/`) to compute Haversine distance from customer saved coordinates or query coordinates.
    - Added radius filtering (`?radius=X`), validating $0 < \text{radius} \le 1000\text{ km}$.
    - Added coordinate range validation ($-90 \le \text{lat} \le 90$, $-180 \le \text{lng} \le 180$).
    - Updated `WorkerPublicDetailView` (`GET /api/workers/<id>/`) to calculate `distance_km` for single worker detail views.
    - Added 9 unit/integration tests in `backend/workers/tests/test_nearby_workers_distance.py`.
  - **Web Frontend**:
    - Updated `WorkerProfile` type with `name`, `latitude`, `longitude`, `location_name`, `distance_km`.
    - Updated `api.nearbyWorkers()` with `lat`, `lng`, `radius` parameters.
    - Customer Dashboard automatically passes customer's saved coordinates (`session.user.latitude`, `session.user.longitude`).
    - Worker list cards display `📍 Location • X.X km away`.
    - Worker detail panel displays `📍 Location • X.X km away`.
  - **Mobile Frontend**:
    - Updated `WorkerProfile` type and `api.nearbyWorkers()` in React Native/Expo app.
    - `CustomerHome` passes customer saved coordinates to `nearbyWorkers`.
    - Worker cards and booking screens display `📍 Location • X.X km away`.

---

## [Feature] Automatic Service Location in Customer Worker Booking
- **Date**: August 2026
- **Status**: Completed & Verified
- **Scope**:
  - Added `service_location_source` to `Booking` model (`saved`, `gps`, `manual`).
  - Pre-fills booking address with customer's saved location.
  - Added one-click GPS capture with Geoapify reverse geocoding in booking form.
  - Stored immutable snapshot of coordinates on booking creation.

---

## [Feature] Smart Registration & Profile Geocoding
- **Date**: August 2026
- **Status**: Completed & Verified
- **Scope**:
  - Integrated Geoapify Geocoding API (`backend/accounts/services/geocoding.py`).
  - Added `location_source` field to `User` model (`gps`, `manual`).
  - Implemented `POST /api/auth/geocode/` and `PATCH /api/auth/location/` endpoints.
  - Added GPS capture & Manual entry toggles in Web and Mobile registration and profile edit screens.
