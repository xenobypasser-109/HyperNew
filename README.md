# HyperXeno

## Backend setup

1. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your values:

   ```powershell
   Copy-Item .env.example .env
   ```

   Required:

   ```text
   MONGO_URI=your_mongodb_uri_here
   JWT_SECRET=use_a_long_random_secret_here
   ```

4. Run the backend:

   ```powershell
   py server.py
   ```

The backend uses MongoDB collections for shared users, global data, audit logs, and system state. Do not commit `.env`; it is ignored by `.gitignore`.
