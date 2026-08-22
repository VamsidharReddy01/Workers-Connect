# Selenium E2E Tests Guidelines

This directory contains the results and reports for the Selenium and API E2E test suite of the Workers Bridge project.

## Running Tests Locally

To run the full suite locally:

1. Ensure Chrome is installed on your machine.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install coverage selenium openpyxl
   ```
3. Run the tests from the `backend` directory:
   ```bash
   cd backend
   python manage.py test selenium_tests --verbosity=2
   ```

To run with coverage:
```bash
coverage run manage.py test selenium_tests --verbosity=2
coverage report -m
coverage html
```

## Running the Reports

To regenerate the Excel summary report:
```bash
cd "Selenium Test Results"
python generate_selenium_test_reports.py
```

## CI Integration
The tests run automatically in GitHub Actions on push and PR to main, master, and develop branches. The coverage HTML and inventory Excel report are automatically uploaded as job artifacts.
