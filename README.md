#  Workers App (Service Marketplace)

[![Security Review](https://github.com/VamsidharReddy01/Workers-Connect/actions/workflows/security-review.yml/badge.svg)](https://github.com/VamsidharReddy01/Workers-Connect/actions/workflows/security-review.yml)

A full-stack service marketplace application where users can find and book skilled workers like electricians, plumbers, carpenters, etc.

Built using **Django (Backend) + React/Vite Web + Expo React Native Mobile + PostgreSQL (Database)**.

---

* 🔐 User Authentication (JWT-based)
* 👷 Worker Registration & Profiles
* 🛠️ Service Categories (Electrician, Plumber, etc.)
* 📅 Booking System
* ⭐ Ratings & Reviews
* 🌐 React web app
* 📱 Expo React Native mobile app

---

##  Tech Stack

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL

### Frontend

* React
* TypeScript
* Vite
* Expo React Native

### Tools

* Git & GitHub
* VS Code
* Postman 

---

## 📁 Project Structure

```
workers-app/
├── backend/        # Django API
├── web/            # React + Vite web app
├── mobile/         # Expo React Native app
├── docs/           # Documentation
```

---

## ⚙️ Backend Setup (Django)

### 1. Clone Repository

```
git clone <your-repo-url>
cd workers-app/backend
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file inside `backend/`:

```
SECRET_KEY=your_secret_key

DB_NAME=workers_db
DB_USER=workers_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

### 5. Setup PostgreSQL

* Install PostgreSQL
* Create database:

```
CREATE DATABASE workers_db;
```

* Create user and grant privileges:

```
CREATE USER workers_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE workers_db TO workers_user;
```

---

### 6. Run Migrations

```
python manage.py migrate
```

---

### 7. Run Server

```
python manage.py runserver
```

Backend will run at:

```
http://127.0.0.1:8000/
```

---

## 🌐 Web Setup (React + Vite)

```
cd ../web
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in `web/.env` if Django is not running at `http://127.0.0.1:8000`.

---

## 📱 Mobile Setup (Expo React Native)

```
cd ../mobile
npm install
npm start
```

---

## 👥 Team Setup

Each developer must:

* Create their own `.env` file
* Setup PostgreSQL locally
* Install dependencies

---

## 🔐 Security Notes

* `.env` file is not committed to Git
* SECRET_KEY must be kept private
* Database credentials should never be exposed

---
## 📄 License

This project is open-source and available under the MIT License.

---
