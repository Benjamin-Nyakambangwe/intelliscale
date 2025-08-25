@echo off
cd /d "C:\Users\HP\Documents\projects\eport\intelliscale"
call venv\Scripts\activate
python manage.py runserver 0.0.0.0:80

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo Opening browser...
start http://myapp.local


pause
