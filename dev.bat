@echo off
echo Starting Backend...
start cmd /k "cd backend && venv\Scripts\python -m uvicorn main:app --reload"

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both servers are running! 
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000