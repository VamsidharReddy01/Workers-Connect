# 🧪 Unit Test Suite — Quickstart & Guide

This directory contains the automated test results, Excel reports, and metrics for the **Workers Bridge** backend test suite.

---

## 🚀 How to Run the Unit Tests

### 1. Run the Entire Test Suite (300 Tests)

```powershell
cd "backend"
python manage.py test
```

### 2. Run with Verbose Output

```powershell
cd "backend"
python manage.py test --verbosity=2
```

### 3. Run Tests for a Specific Application

```powershell
# Accounts app tests (116 tests)
python manage.py test accounts

# Workers app tests (127 tests)
python manage.py test workers

# Notifications app tests (31 tests)
python manage.py test notifications

# Config / Settings & Contracts (26 tests)
python manage.py test config
```

### 4. Run a Specific Test Module

```powershell
python manage.py test accounts.tests.test_views
python manage.py test workers.tests.test_booking_status_flow_deep
python manage.py test notifications.tests.test_services
```

---

## 📊 How to Measure Code Coverage

```powershell
# Run with coverage tool
coverage run manage.py test

# Display terminal summary
coverage report -m

# Generate HTML coverage report
coverage html
```

---

## 📑 How to Regenerate the Excel Reports

```powershell
cd "Unit Test Results"
python generate_unit_test_reports.py
```

---

## 📁 Deliverables in this Directory

| File | Description |
|---|---|
| [`unit-tests-inventory.xlsx`](file:///c:/Users/vamsi/OneDrive/Desktop/Worker_App/Unit%20Test%20Results/unit-tests-inventory.xlsx) | Excel workbook with 300 test inventory, module metrics, and quality score. |
| [`test-summary.md`](file:///c:/Users/vamsi/OneDrive/Desktop/Worker_App/Unit%20Test%20Results/test-summary.md) | High-level executive summary of unit test suite and scores. |
| [`unit-test-report.md`](file:///c:/Users/vamsi/OneDrive/Desktop/Worker_App/Unit%20Test%20Results/unit-test-report.md) | Comprehensive deep-dive report listing all 300 test cases. |
| [`test-coverage-report.md`](file:///c:/Users/vamsi/OneDrive/Desktop/Worker_App/Unit%20Test%20Results/test-coverage-report.md) | Component-by-component and endpoint coverage breakdown. |
| [`generate_unit_test_reports.py`](file:///c:/Users/vamsi/OneDrive/Desktop/Worker_App/Unit%20Test%20Results/generate_unit_test_reports.py) | Python generator script for Excel workbooks. |
