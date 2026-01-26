# GiftGenius Backend

GiftGenius is a relationship management system designed to help users capture unstructured memories about friends and loved ones, serving as a "Second Brain" for relationships. This repository contains the backend API built with FastAPI and PostgreSQL.

## 🚀 Features (Phase 1)

-   **User Authentication**: Secure registration and login using JWT and Bcrypt.
-   **Contact Management**: Create, view, update, and delete contacts with relationship details.
-   **Memory Logging**: Capture and retrieve text-based memories for each contact.
-   **Data Persistence**: Robust data storage using PostgreSQL and Docker volumes.
-   **API Documentation**: Auto-generated interactive documentation via Swagger UI.

## 🛠️ Tech Stack

-   **Language**: Python 3.10+
-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - High-performance, easy-to-learn, fast to code, ready for production.
-   **Database**: [PostgreSQL 15](https://www.postgresql.org/) - The world's most advanced open source relational database.
-   **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases in Python, designed to simplify interaction with the database.
-   **Authentication**: JWT (JSON Web Tokens) & Passlib (Bcrypt).
-   **Containerization**: Docker & Docker Compose.

## 📂 Project Structure

```
giftgenius-backend/
├── app/
│   ├── api/            # API endpoints (Auth, Contacts, Memories)
│   ├── core/           # Core utilities (Config, Security)
│   ├── database.py     # Database connection & session handling
│   ├── main.py         # Application entry point
│   ├── models.py       # SQLModel database tables
│   └── schemas.py      # Pydantic request/response models
├── docs/               # Project documentation
├── .env.example        # Environment variables template
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Backend container definition
└── requirements.txt    # Python dependencies
```

## ⚡ Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/get-started) and Docker Compose installed on your machine.

### Installation & Running

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd giftgenius-backend
    ```

2.  **Configure Environment Variables**
    Copy the example environment file and update it with your settings (if needed).
    ```bash
    cp .env.example .env
    ```
    *Note: The default settings in `.env.example` are sufficient for local development.*

3.  **Start the Application**
    Run the following command to build and start the backend and database containers:
    ```bash
    docker-compose up --build
    ```

4.  **Access the API**
    -   **API Root**: `http://localhost:8000`
    -   **Interactive Docs (Swagger UI)**: `http://localhost:8000/docs`
    -   **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`

## 🧪 API Endpoints Overview

### Authentication
-   `POST /api/v1/auth/register`: Register a new user.
-   `POST /api/v1/auth/login`: Login and retrieve an access token.

### Contacts
-   `GET /api/v1/contacts`: List all contacts.
-   `POST /api/v1/contacts`: Create a new contact.
-   `GET /api/v1/contacts/{id}`: Get specific contact details.
-   `DELETE /api/v1/contacts/{id}`: Delete a contact.

### Memories
-   `GET /api/v1/contacts/{id}/memories`: List memories for a contact.
-   `POST /api/v1/contacts/{id}/memories`: Add a memory for a contact.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

[MIT](LICENSE)