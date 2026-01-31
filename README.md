# GiftGenius Backend

AI-powered gift recommendation system backend built with FastAPI and Supabase.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Supabase account and project ([sign up here](https://supabase.com))

### 1. Clone and Setup

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

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Get your Supabase credentials from:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_ANON_KEY`

Your `.env` should look like:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SECRET_KEY=your-generated-secret-key
```

Generate a SECRET_KEY:
```bash
openssl rand -hex 32
```

### 3. Run the Application

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
│   │   ├── supabase.py      # Supabase client initialization
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

### Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **Table Editor**
3. Create tables for your application:
   - `users` - User accounts
   - `contacts` - User contacts
   - `memories` - Contact memories

### Example: Create Users Table

In Supabase SQL Editor, run:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔐 Security

- **Never commit `.env` file** - It's already in `.gitignore`
- **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
- **Enable Row Level Security (RLS)** in Supabase for production
- **Use SUPABASE_ANON_KEY** for client-side apps
- **Never expose SUPABASE_SERVICE_ROLE_KEY** to clients

## 🧪 Testing

### Test Supabase Connection

```python
from app.core.supabase import supabase

# List tables
response = supabase.table("users").select("*").limit(5).execute()
print(response.data)
```

### Test API Endpoints

Visit http://localhost:8000/docs and use the interactive Swagger UI.

## 📦 Dependencies

- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Supabase** - Backend-as-a-Service client
- **Python-Jose** - JWT token handling
- **Passlib** - Password hashing
- **Pydantic** - Data validation

## 🚢 Deployment

### Environment Variables

Ensure these are set in your production environment:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
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

### Supabase connection errors

1. Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
2. Verify Supabase project is active (not paused)
3. Check network connection

### Port already in use

```bash
# Use a different port
uvicorn app.main:app --reload --port 3000
```

## 📞 Support

For issues and questions:
- Check the [documentation](docs/)
- Review [Supabase docs](https://supabase.com/docs)
- Review [FastAPI docs](https://fastapi.tiangolo.com)

---

**Built with ❤️ using FastAPI and Supabase**