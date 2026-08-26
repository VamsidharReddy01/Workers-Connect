# WorkersBridge - Project Brain & Architecture Guide

## Overview
WorkersBridge is a full-stack platform connecting local skilled service workers (carpenters, plumbers, electricians, cleaners, etc.) with customers for home and on-demand services.

## Architecture

### Backend
- **Framework**: Django 6.0 with Django REST Framework (DRF)
- **Database**: PostgreSQL (with SQLite for in-memory fast testing)
- **Authentication**: JWT authentication with refresh token blacklisting and role-based permissions (`worker` vs `customer`).
- **Geocoding & Location Services**:
  - Provider: Geoapify API (`https://api.geoapify.com/v1/geocode/reverse` and `https://api.geoapify.com/v1/geocode/search`)
  - Utilities: `backend/accounts/services/geocoding.py` with caching, timeout protection, coordinate validation, and fallback handling.
  - Coordinate Precision: 6 decimal places (~0.1m precision).
  - Spatial Indexing: Composite B-Tree index on `(latitude, longitude)` in `accounts_user`.

### Frontend
- **Web**: React 19 + TypeScript + Vite + Lucide React
- **Mobile**: React Native + Expo + TypeScript
- **State & Communication**: REST APIs with JWT authentication tokens.

## Location Architecture & Features

### 1. Smart Registration & Profile Geocoding
- **GPS Capture**: Browser `navigator.geolocation` and Expo `Location.getCurrentPositionAsync` obtain exact device coordinates.
- **Geoapify Reverse Geocoding**: Resolves GPS coordinates to human-readable address.
- **Manual Input Geocoding**: Forward geocodes typed addresses to coordinates.
- **Storage**: `location_source` (`gps` / `manual`), `latitude`, `longitude`, `location_permission_granted`, `location_updated_at`.

### 2. Automatic Service Location in Booking
- **Prefilling**: Automatically pre-fills service address from customer's saved location profile.
- **GPS Override**: Allows one-tap capture of current service location.
- **Snapshot Integrity**: Freezes `service_latitude`, `service_longitude`, and `service_location_source` (`saved` | `gps` | `manual`) on the booking record at creation time.

### 3. Nearby Workers with Distance & Radius Filtering
- **Endpoint**: `GET /api/workers/nearby/` (and alias `GET /api/workers/`)
- **Query Parameters**:
  - `latitude` / `lat`: Customer origin latitude (-90 to 90)
  - `longitude` / `lng`: Customer origin longitude (-180 to 180)
  - `radius`: Search radius in kilometers (default: unlimited/all or configurable up to 1000 km)
  - `category`: Service category filter (case-insensitive)
  - `search`: Full text search across worker username, category, and location
  - `available_only`: Online availability filter (`true` / `1` / `yes`)
- **Default Origin Resolution**:
  - If authenticated customer calls endpoint without query coordinates, backend automatically uses `request.user.latitude` and `request.user.longitude`.
- **Distance Formula**: Haversine formula in `_haversine_km(lat1, lon1, lat2, lon2)` with spherical earth radius $R = 6371.0\text{ km}$.
- **Sorting**: Prioritizes online workers (`is_online=True`), then sorted ascending by `distance_km` (nearest first).
- **Worker Object Schema**:
  ```json
  {
    "id": 12,
    "name": "Ravi Kumar",
    "category": "Carpenter",
    "price": "50.00",
    "rating": 4.9,
    "total_reviews": 100,
    "experience_years": 5,
    "is_online": true,
    "latitude": "17.443500",
    "longitude": "78.377200",
    "location_name": "HITEC City, Hyderabad",
    "distance_km": 1.54,
    "user": {
      "id": 12,
      "username": "Ravi Kumar",
      "role": "worker",
      "masked_location": "HITEC City, Hyderabad",
      "profile_photo_url": null
    }
  }
  ```
- **UI Integration**:
  - Web Customer Dashboard: Worker cards render `📍 Location • X.X km away`; worker detail panel shows distance.
  - Mobile Customer Home: Worker cards and booking cards render `📍 Location • X.X km away`.

### 4. Worker vs Customer Signup & Role Provisioning
- **Endpoints**:
  - `POST /api/auth/worker-signup/` (and `POST /api/auth/signup/worker/`): Dedicated endpoint that registers users with `role='worker'` and automatically provisions their `WorkerProfile` with chosen category.
  - `POST /api/auth/customer-signup/` (and `POST /api/auth/signup/customer/`): Dedicated endpoint that registers users with `role='customer'`.
  - `POST /api/auth/signup/`: Supports both `role='customer'` and `role='worker'`.
- **UI Differentiation**:
  - **Worker Signup**: Highlights **"Wanna Join as Worker?"**, displaying a distinct Pro Worker badge, primary trade selector, service base location with GPS geocoding, and green/emerald professional accent styling.
  - **Customer Signup**: Displays Customer account creation with a prominent `"Wanna Join as Worker?"` switcher banner to allow service providers to easily register.
