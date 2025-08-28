VideoShare Demo — Login + Sign up (FastAPI backend)

How to run (Linux/Mac/WSL):
1) Create & activate a virtual environment (recommended)
   python -m venv .venv && . .venv/bin/activate

2) Install dependencies
   pip install -r requirements.txt

3) Start the API (port 8000)
   uvicorn main:app --reload --port 8000

4) Serve the frontend (port 5500 for example)
   cd (this folder) and run:  python -m http.server 5500
   Then open:  http://localhost:5500/index.html

The frontend auto-detects the API at :8000 based on the current origin/port.
To override, you can set a custom base URL in the browser console:
   localStorage.setItem('API_BASE', 'http://127.0.0.1:8000')

Endpoints:
- POST /auth/register  {email, name, password} -> creates user
- POST /auth/login (form fields: username, password) -> returns JWT + user
- GET  /videos/latest
- GET  /videos?q=term

Database:
- SQLite file videoshare.db is created automatically with sample videos.
- Update SECRET_KEY in main.py for production.
