# SBU Mess Management System

A digital mess management system for Sarala Birla University that streamlines meal booking, menu planning, inventory tracking, payments, announcements, and feedback across student, staff, and admin roles.

## Project Overview

The SBU Mess Management System replaces manual mess operations with a modern web application.

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
- Database: SQLite (development), PostgreSQL (production-ready)
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
4. Create a `.env` file at the repository root if you need to override default values.
   Example settings:
   ```text
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///mess_management.db
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=noreply@sbumess.edu
   ```
5. Run the application:
   ```powershell
   python run.py
   ```
6. Open the app in a browser:
   ```text
   http://127.0.0.1:5000
   ```

## Demo Credentials

- Admin: `admin` / `admin123`
- Staff: `staff` / `staff123`
- Student: `student1` / `student123`

## Notes

- The repository already ignores environment files such as `.env` and `.env.*`.
- Use `.env` for sensitive credentials and do not commit secret values to Git.

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
