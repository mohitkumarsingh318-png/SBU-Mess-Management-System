
@echo off
echo ==========================================
echo SBU Mess Management System
echo ==========================================
echo.


echo.
echo Starting the application...
echo Open your browser and go to: http://127.0.0.1:5000
echo.
echo Login Credentials:
echo Admin:     username=admin     password=admin123
echo Staff:     username=staff     password=staff123
echo Student:   username=student1  password=student123
echo.
echo Press CTRL+C to stop the server
echo.

venv\Scripts\python.exe run.py

echo.
echo Server stopped.
pause