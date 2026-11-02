# Mess Management System

A digital mess management system that streamlines meal booking, menu planning, inventory tracking, payments, announcements, and feedback across student, staff, and admin roles.

## Project Overview

The Mess Management System replaces manual mess operations with a modern web application.

- Students can book meals, view menus, track payments, and submit feedback.
- Staff can verify meals, monitor meal counts, and manage inventory.
- Admins can create menus, manage users, view reports, and oversee system operations.

## Key Features

- Multi-role access: student, staff, and admin dashboards
- Meal booking and verification
- Weekly menu management
- Payment tracking and reporting
- Inventory management with low-stock alerts
- Feedback and announcement system
- Daily and monthly reports
- Email notification support
- Secure login and role-based access control

## Technology Stack

- Backend: Flask (Python)
- Database: SQLAlchemy with SQLite for local development or MySQL for deployment
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript
- ORM: SQLAlchemy

## Setup Instructions

1. Clone the repository.
2. Create and activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate.bat
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`. To use MySQL, first create a database with your database provider, then set the connection URL in `.env`:
   ```text
   DATABASE_URL=mysql+pymysql://username:password@host:3306/database_name
   ```
   Replace the placeholders with the values from your MySQL provider. URL-encode special characters in the password. Keep `.env` private; for Render, configure `DATABASE_URL` as a service environment variable and allow the app host to connect to the database. If `DATABASE_URL` is unset, the app uses its local SQLite database.
5. Run the application:
   ```powershell
   python run.py
   ```
6. Open the app in a browser:
   ```text
   http://127.0.0.1:5000
   ```

## Render Deployment

The `.python-version` file pins the Render runtime to Python 3.12.8 for compatibility with the dependencies. Use `pip install -r requirements.txt` as the build command and `gunicorn run:app --bind 0.0.0.0:$PORT` as the start command.

After deploying, run `flask --app run create-admin` in the Render Shell to create an administrator; the password is entered privately and must be at least 12 characters. If the database was previously initialized with demo accounts, run `flask --app run disable-demo-accounts` to deactivate those accounts without deleting their associated data. New student accounts can register through the app.

## Notes

- The repository already ignores environment files such as `.env` and `.env.*`.
- Use `.env` for sensitive credentials and do not commit secret values to Git.
- The app creates missing tables on startup, but switching from SQLite to MySQL does not copy existing records. Back up or migrate any data you need to keep.

## Documentation

Additional documentation files include:
- `PROJECT_INTRODUCTION.md`
- `QUICK_START.md`
- `A2Z_DOCUMENTATION.md`
- `TIER1_FEATURES_DOCUMENTATION.md`
- `EMAIL_CONFIGURATION.md`
- `PROJECT_STATUS_REPORT.md`

## License

Use the project according to your institution or organization guidelines.
