#  Workers App (Service Marketplace)

A full-stack service marketplace application where users can find and book skilled workers like electricians, plumbers, carpenters, etc.

Built using **Django (Backend) + Flutter (Frontend) + PostgreSQL (Database)**.

---

* 🔐 User Authentication (JWT-based)
* 👷 Worker Registration & Profiles
* 🛠️ Service Categories (Electrician, Plumber, etc.)
* 📅 Booking System
* ⭐ Ratings & Reviews
* 📱 Cross-platform Mobile App (Flutter)

---

##  Tech Stack

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL

### Frontend

* Flutter
* Dart

### Tools

* Git & GitHub
* VS Code
* Postman 

---

## 📁 Project Structure

```
workers-app/
├── backend/        # Django API
├── frontend/       # Flutter app
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

## 📱 Frontend Setup (Flutter)

```
cd ../frontend
flutter pub get
flutter run
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
