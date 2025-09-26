# Spot Check

A full-stack application for discovering restaurants near you, saving favorites, and leaving reviews.

This repository contains the Flask backend and a React (Vite) frontend located in `client_code/`.

## Tech Stack
- **Backend**: `Flask`, `Flask-RESTful`, `Flask-SQLAlchemy`, `Flask-Migrate`, `PyJWT`, `Flask-CORS`
- **Database**: `SQLite` (default: `spotcheck.db`)
- **Frontend**: `React 19` + `Vite` + `Tailwind CSS`
- **External API**: Google Places API

## Repository Structure
- `src/` — Flask backend source
  - `app.py` — app entry, API route registration
  - `endpoints.py` — REST resources and handlers
  - `models.py` — SQLAlchemy models
  - `migrations/` — Alembic/Flask-Migrate artifacts
- `client_code/` — React frontend (Vite)
- `Pipfile` / `Pipfile.lock` — Python dependencies (pipenv)

---
## Prerequisites
- Python 3.8
- Node.js 18+ and npm
- pipenv (`pip install pipenv`) or use your preferred venv manager
- A Google Cloud API key enabled for Places API

## Environment Variables
Create a `.env` file at the project root with the following keys:

```env
# Required for Google Places nearby search
GOOGLE_CLOUD_API_KEY=your-google-places-api-key
```
---
## Backend Setup (Flask)

1. Install dependencies and activate the virtual environment:
    ```bash
    pipenv install
    pipenv shell
    ```
2. Set Flask environment variables in src:
    ```bash
    export FLASK_APP=app.py
    ```
3. Initialize and apply database migrations:
    ```bash
    flask db init   # only the first time if migrations folder doesn't exist
    flask db migrate -m "init"
    flask db upgrade
    ```
    The app uses a local SQLite database at `sqlite:///spotcheck.db` by default.
4. Run the server:
    ```bash
    flask run
    ```
    By default, this starts at `http://127.0.0.1:5000`.

---
## Frontend Setup (React + Vite)

1. Install dependencies:
    ```bash
    cd client_code
    npm install
    ```
2. Start the dev server:
    ```bash
    npm run dev
    ```
    Vite will output a local URL such as `http://127.0.0.1:5173`.

If your frontend needs to call the backend, ensure it targets `http://127.0.0.1:5000` (or your configured host/port). You may create a `.env` inside `client_code/` (e.g., `VITE_API_BASE_URL=http://127.0.0.1:5000`).

---
## API Overview
Base URL: `http://127.0.0.1:5000`

- `POST /users`
  - Create a user. Required body: `email`, `username`, `password`, `first_name`, `last_name`.
  - Returns: `{ user, token, message }`.
- `GET /users/<id>`
  - Get user by id.
- `PATCH /users/<id>`
  - Update user fields.
- `DELETE /users/<id>`
  - Delete a user.
- `POST /login`
  - Authenticate user. Body: `email`, `password`.
  - Returns: `{ user, token, message }` (JWT token).
- `GET /places?latitude=<lat>&longitude=<lng>`
  - Proxies to Google Places Nearby Search for restaurants using `GOOGLE_CLOUD_API_KEY`.
- `POST /places`
  - Persist a place returned from Google Places to the local DB. Accepts either a `place` object (from Google response) or a compatible payload.
- `GET /places/<id>`
  - Fetch a single place by local id.
- `GET /favorites` (auth)
  - Get the authenticated user's favorite places.
- `POST /favorites` (auth)
  - Body: `{ place_id }`. Adds a place to favorites (idempotent).
- `DELETE /favorites/<id>` (auth)
  - Remove a favorite by favorite id (must belong to current user).
- `POST /places/<place_id>/add_review` (auth)
  - Create a review for a place. Required fields: `rating (1-5)`, `title`, `content`, `visit_date` (ISO `YYYY-MM-DD`).
- `PATCH /reviews/<id>` (auth)
  - Update a review (must belong to current user).
- `DELETE /reviews/<id>` (auth)
  - Delete a review (must belong to current user).

Authentication uses the `Authorization: Bearer <token>` header with the JWT returned by `/login` or `/users`.


## Notes
- Ensure `.env` is configured with valid `GOOGLE_CLOUD_API_KEY` before calling authenticated or Places endpoints.

---
## License
See `LICENSE` for details.