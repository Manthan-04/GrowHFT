# HFT Trading API — Local Setup Guide (Windows)

Complete step-by-step instructions to run the HFT Trading API on your local Windows machine.

---

## Prerequisites

### 1. Install Python 3.11+

- Download from: https://www.python.org/downloads/
- **Important:** During installation, check the box **"Add Python to PATH"**
- Verify installation by opening Command Prompt:
  ```
  python --version
  ```
  You should see something like `Python 3.11.x`

### 2. Install PostgreSQL

- Download from: https://www.postgresql.org/download/windows/
- Run the installer and set a password for the `postgres` user (remember this password)
- After installation, open Command Prompt and create the database:
  ```
  psql -U postgres
  ```
  Enter your password when prompted, then run:
  ```sql
  CREATE DATABASE hft_trading;
  \q
  ```

---

## Project Setup

### 3. Download the Project Files

Download all files from the `server/python/` folder to a local directory, for example `C:\hft-trading\`.

Your folder structure should look like this:

```
C:\hft-trading\
├── main.py
├── engine.py
├── strategies.py
├── indicators.py
├── money_management.py
├── database.py
├── schemas.py
├── config.py
├── requirements.txt
└── static\
    └── index.html
```

### 4. Install Python Dependencies

Open Command Prompt and navigate to the project folder:

```
cd C:\hft-trading
```

Install all required packages:

```
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pandas numpy
```

### 5. Create the Environment File

Create a file called `.env` inside `C:\hft-trading\` with the following content:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/hft_trading
```

Replace `YOUR_PASSWORD` with the password you set during PostgreSQL installation.

---

## Running the Application

### 6. Start the Server

In Command Prompt, from the project folder:

```
cd C:\hft-trading
python main.py
```

You should see output like:

```
Starting HFT Trading API...
INFO:     Connected to database
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
Engine auto-started in background
INFO:     Outside market hours. Sleeping 60 s...
```

### 7. Open the Dashboard

- Open your browser and go to: **http://localhost:5000**
- The admin dashboard will load automatically
- Interactive API docs are available at: **http://localhost:5000/docs**

---

## What to Expect

- The trading engine **auto-starts** when the server boots
- Without Groww API keys, the engine runs in **SIMULATION mode** with generated price data
- During **NSE market hours (9:15 AM – 3:30 PM IST, weekdays)**, the engine scans all 10 symbols every 5 seconds
- Outside market hours, the engine sleeps and checks every 60 seconds

---

## Optional: Enable Live Trading

If you want to connect to the Groww trading platform for live trading, add these to your `.env` file:

```
GROWW_API_KEY=your_groww_api_key_here
GROWW_API_SECRET=your_groww_api_secret_here
```

Without these keys, everything works in simulation mode, which is fine for testing and development.

---

## Quick Reference — All Commands

```bash
# Step 1: Verify Python is installed
python --version

# Step 2: Create PostgreSQL database
psql -U postgres
CREATE DATABASE hft_trading;
\q

# Step 3: Navigate to project folder
cd C:\hft-trading

# Step 4: Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pandas numpy

# Step 5: Create .env file with your DATABASE_URL
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/hft_trading

# Step 6: Start the server
python main.py

# Step 7: Open in browser
# http://localhost:5000          (Dashboard)
# http://localhost:5000/docs     (API Documentation)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` command not found | Reinstall Python and check "Add to PATH" |
| `psql` command not found | Add PostgreSQL bin folder to your system PATH (e.g., `C:\Program Files\PostgreSQL\15\bin`) |
| Database connection error | Verify your `.env` file has the correct password and that PostgreSQL is running |
| Port 5000 already in use | Either stop the other process using port 5000, or change the port by adding `PORT=8000` to your `.env` file |
| `ModuleNotFoundError` | Run `pip install <module_name>` for the missing module |

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Admin Dashboard |
| GET | `/api/status` | API status and engine state |
| GET | `/api/users` | List all users |
| GET | `/api/users/{id}` | Get specific user |
| GET | `/api/strategies` | List all strategies |
| GET | `/api/trades` | List all trades (filter with `?user_id=X`) |
| GET | `/api/engine/status` | Engine running status |
| GET | `/api/engine/signals` | Auto-generated trading signals |
| GET | `/api/engine/metrics` | Risk metrics (win rate, drawdown, etc.) |
| GET | `/api/symbols` | Default tracked symbols |
| GET | `/docs` | Interactive API documentation |
