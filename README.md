# GiftGenius Backend

AI-powered gift recommendation system backend built with FastAPI and PostgreSQL.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (for local PostgreSQL)

### 1. Start PostgreSQL with Docker

**Docker Desktop must be running** (otherwise you get `dockerDesktopLinuxEngine: The system cannot find the file specified`).

From the project root, run the setup script (starts Postgres in background, creates tables, verifies inside Docker):

```powershell
.\scripts\setup-postgres.ps1
```

This script:
- Starts the Postgres container in the background (`docker compose up -d`)
- Waits until Postgres is ready
- Runs the migration **inside the container** to create tables
- **Verifies tables** with a query run **inside Docker only**: `docker exec giftgenius-postgres psql ... -c "SELECT table_name FROM information_schema.tables ..."`

Manual alternative (same credentials):
- **User:** `prince1314` | **Password:** `@Prince1314` | **Database:** `giftgenius` | **Port:** `5432`
- Create tables: `Get-Content migrations\001_create_tables.sql | docker exec -i giftgenius-postgres psql -U prince1314 -d giftgenius`
- Verify: `docker exec giftgenius-postgres psql -U prince1314 -d giftgenius -c "\dt"`

### 2. Clone and Setup

```bash
# Navigate to project directory
cd giftgenius-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`: set `DATABASE_URL` (already correct for Docker if you use user `prince1314` and password `@Prince1314`). The `@` in the password must be written as `%40` in the URL:

```
DATABASE_URL=postgresql://prince1314:%40Prince1314@localhost:5432/giftgenius
```

Generate a `SECRET_KEY` for JWT:

```bash
openssl rand -hex 32
```

### 4. Run the Application

```bash
# Make sure virtual environment is activated
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
giftgenius-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration settings
│   │   ├── database_init.py # PostgreSQL table checks and migration helper
│   │   └── security.py      # JWT and authentication (to be added)
│   └── api/
│       └── v1/
│           ├── __init__.py
│           ├── auth.py      # Authentication endpoints (to be added)
│           ├── contacts.py  # Contact management (to be added)
│           └── memories.py  # Memory management (to be added)
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt         # Python dependencies
└── README.md
```

## 🔧 Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Development Server

```bash
uvicorn app.main:app --reload
```

The `--reload` flag enables auto-reload on code changes.

### Run on Different Port

```bash
uvicorn app.main:app --reload --port 3000
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

#### Health Check
```http
GET /
```
Returns API status and version.

```http
GET /health
```
Returns detailed health check including database connection status.

## 🗄️ Database Setup

PostgreSQL runs via Docker (see Quick Start). Tables are created by running `migrations/001_create_tables.sql` once. To run it again (idempotent):

```bash
docker exec -i giftgenius-postgres psql -U prince1314 -d giftgenius < migrations/001_create_tables.sql
```

## 🔐 Security

- **Never commit `.env` file** - It's already in `.gitignore`
- **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
- Use a strong `SECRET_KEY` and keep `.env` out of version control

## 🧪 Testing

### Test PostgreSQL Connection

```bash
# From host
docker exec -it giftgenius-postgres psql -U prince1314 -d giftgenius -c "SELECT 1;"
```

### Test API Endpoints

Visit http://localhost:8000/docs and use the interactive Swagger UI.

## 📦 Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **PostgreSQL** - Database (via SQLModel/psycopg2)
- **Python-Jose** - JWT token handling
- **Passlib** - Password hashing
- **Pydantic** - Data validation

## 🚢 Deployment

### Environment Variables

Ensure these are set in your production environment:
- `DATABASE_URL` (PostgreSQL connection string)
- `SECRET_KEY`
- `ENVIRONMENT=production`
- `DEBUG=False`

### Run Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For production, consider using:
- **Gunicorn** with Uvicorn workers
- **Docker** containerization
- **Railway**, **Render**, or **Vercel** for hosting

## 📖 Documentation

For detailed implementation guide, see:
- [Implementation Plan](docs/implementation_plan.md)
- [Backend Structure](docs/backend_structure.md)
- [Supabase Setup Guide](docs/supabase_setup.md) (if available)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Troubleshooting

### Virtual environment not activating

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Module not found errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database connection errors

1. **Docker not running:** Start Docker Desktop (Windows/Mac) or the Docker daemon. Then run `docker compose up -d`.
2. Ensure Docker Postgres is running: `docker compose ps`
3. Check `DATABASE_URL` in `.env` (password `@` must be `%40` in the URL)
4. Confirm tables exist: run `migrations/001_create_tables.sql` once (see Database Setup)

### Port already in use

```bash
# Use a different port
uvicorn app.main:app --reload --port 3000
```

## 📞 Support

For issues and questions:
- Check the [documentation](docs/)
- Review [PostgreSQL docs](https://www.postgresql.org/docs/)
- Review [FastAPI docs](https://fastapi.tiangolo.com)

---

**Built with ❤️ using FastAPI and PostgreSQL**