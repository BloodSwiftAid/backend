# SwiftAid Backend API

The SwiftAid backend powers the core operations for blood banks, hospitals, and public users, managing inventories, real-time requests, payments, and notifications.

## Prerequisites

- **Python**: 3.12 or higher
- **PostgreSQL**: Running locally or via Docker
- **Redis**: Running locally (for background tasks & WebSockets)
- **uv**: (Recommended) Fast Python package installer and resolver.

## Local Setup

1. **Navigate to the backend directory**
   ```bash
   cd app/backend
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   uv pip install -r requirements.txt
   # Alternatively, if using pyproject.toml:
   uv pip install -e .
   ```

4. **Environment Variables**
   Create a `.env` file in the `backend/` directory based on the `.env.example` file (if available) or by referring to `core/settings/components/common.py`. Key variables include:
   - `SECRET_KEY`
   - `DATABASE_URL` (e.g., `postgres://user:password@localhost:5432/swiftaid`)
   - `REDIS_HOST`, `REDIS_PORT`
   - `CORS_ALLOWED_ORIGINS`

5. **Database Setup**
   Run the initial migrations to set up your PostgreSQL database.
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**
   Since we use Django Channels, Daphne is the ASGI server handling HTTP and WebSocket traffic.
   ```bash
   python manage.py runserver
   ```
   *The server will be available at `http://localhost:8000`.*

8. **Running Background Tasks (RQ Worker)**
   In a separate terminal, start the worker to handle async tasks:
   ```bash
   python manage.py rqworker default sender
   ```

## Documentation

Once the server is running, the Swagger UI for the API is available at:
`http://localhost:8000/api/schema/swagger-ui/`
