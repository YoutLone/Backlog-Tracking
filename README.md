# Backlog Tracking API

A production-minded FastAPI for agile teams to manage shared product backlogs. It supports user authentication, team-based multi-tenancy, backlog item workflow tracking, prioritisation, and lightweight sprint planning.

Built for the backend technical brief using **FastAPI** and **Supabase Postgres**.

## Contents

- [Feature Coverage](#feature-coverage)
- [Tech Stack](#tech-stack)
- [Live Demo](#live-demo)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Run the API](#run-the-api)
- [API Endpoint Summary](#api-endpoint-summary)
- [Testing](#testing)
- [Design Notes](#design-notes)
- [Production Next Steps](#production-next-steps)
- [Author](#author)
- [License](#license)

## Feature Coverage

### Core requirements

- **Authentication**: register and login with email/password, returning a JWT bearer token.
- **Password safety**: passwords are hashed with Argon2 and never stored in plain text.
- **Teams / multi-tenancy**: users can create teams and belong to one or more teams.
- **Server-side authorization**: backlog and sprint access is checked through team membership before reads or writes.
- **Backlog items**: team members can create, read, update, delete, move, assign to sprint, and reorder backlog items.
- **Filtering and pagination**: backlog list supports `status`, `type`, `sprint_id`, `assigned_to`, `limit`, and `offset`.
- **Priority ordering**: backlog items are returned by `priority_rank` ascending.
- **Workflow movement**: item status changes go through an explicit status endpoint.
- **Sprints**: team members can create sprints, assign items to sprints, and list sprint details with items.
- **OpenAPI docs**: FastAPI documentation is available at `/docs` or `/redoc`.
- **Schema from scratch**: database setup is provided in `migrations/001_initial_schema.sql`.

### Bonus items included

- Legal status transition validation.
- Activity log / audit trail for backlog and sprint changes.
- Sprint aggregates: item count, total story points, and completed story points.
- Docker and Docker Compose support.
- Pytest test structure for auth, team membership, and backlog workflow behavior.

## Tech Stack

- **Python**: 3.11+
- **Framework**: FastAPI
- **Database**: Supabase-hosted PostgreSQL
- **Database driver**: `asyncpg`
- **Authentication**: JWT via `python-jose`
- **Password hashing**: Argon2 via `passlib[argon2]`
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio, httpx
- **Runtime**: Uvicorn
- **Package management**: uv
- **Containerization**: Docker, Docker Compose


## Live Demo 

- **API Base URL**: `https://backlog-tracking.onrender.com`
- **Interactive Docs**: [https://backlog-tracking.onrender.com/docs](https://backlog-tracking.onrender.com/docs)
- **Health Check**: [https://backlog-tracking.onrender.com/health](https://backlog-tracking.onrender.com/health)

## Project Structure

```text
app/
  api/
    dependencies.py        # JWT user dependency and auth guard
    routes/                # FastAPI routers
  core/
    config.py              # Environment-based settings
    security.py            # Password hashing and JWT helpers
  db/
    database.py            # asyncpg pool and startup initialization
  repositories/            # SQL data access layer
  schemas/                 # Pydantic request/response models
  services/                # Business rules and authorization checks
  main.py                  # FastAPI app, middleware, route registration
migrations/
  001_initial_schema.sql   # Full PostgreSQL schema
tests/                     # Unit and integration tests
Dockerfile
docker-compose.yml
Makefile
requirements.txt
pyproject.toml
run.py
```

## Quick Start

### 1. Clone and enter the project

```bash
git clone https://github.com/YoutLone/Backlog-Tracking.git
cd Backlog-Tracking
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If you already have `uv` installed, verify it with:

```bash
uv --version
```

### 3. Create environment and install dependencies

```bash
uv sync --extra dev
```

### 4. Create local environment file

```bash
cp .env.example .env
```

Update `.env` with your Supabase PostgreSQL connection string and a strong JWT secret.

### 5. Apply the database schema

Run `migrations/001_initial_schema.sql` in the Supabase SQL editor, or apply it with `psql`:

```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
```

### 6. Start the API

```bash
uv run uvicorn app.main:app --reload
```

Open:

- API health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

Create `.env` from `.env.example`.

| Variable | Required | Example | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql://postgres.reqxxbyhiirekkzzbyvi:[YOUR-PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres` | Supabase Postgres connection string. Use the pooled connection if needed. |
| `JWT_SECRET_KEY` | Yes | `change-me-to-a-long-random-secret` | Must be strong and private in production. |
| `JWT_ALGORITHM` | No | `HS256` | Defaults to `HS256`. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Defaults to one day. |
| `APP_ENV` | No | `development` | Controls development behavior such as permissive CORS. |
| `DEBUG` | No | `true` | Local debug flag. |

Do not commit `.env` or real secrets.

## Database Setup

This project uses application-managed authentication tables instead of Supabase Auth. Supabase is used as the hosted PostgreSQL database.

The schema creates:

- `users`
- `teams`
- `team_members`
- `sprints`
- `backlog_items`
- `activity_log`
- indexes for team-scoped lookups and backlog ordering
- `updated_at` triggers

### Supabase setup

1. Create a free Supabase project.
2. Go to **SQL Editor**.
3. Paste and run `migrations/001_initial_schema.sql`.
4. Copy the PostgreSQL connection string into `DATABASE_URL`.
5. Start the FastAPI app.

The app also checks on startup whether the `users` table exists and attempts to run the initial migration if the schema is missing. 

### Local development

```bash
uv run uvicorn app.main:app --reload
```

### With `run.py`

```bash
uv run python run.py
```

### With Docker Compose

```bash
docker-compose up --build
```

Useful Makefile commands:

```bash
make build
make up
make up-d
make logs
make down
```

## API Endpoint Summary

### Authentication

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Register a user |
| `POST` | `/api/auth/login` | Login and receive JWT |

### Teams

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/teams/` | Create a team |
| `GET` | `/api/teams/` | List current user's teams |
| `GET` | `/api/teams/{team_id}` | Get team details |
| `PUT` | `/api/teams/{team_id}` | Update team |
| `DELETE` | `/api/teams/{team_id}` | Delete team |
| `POST` | `/api/teams/{team_id}/members` | Add team member |
| `GET` | `/api/teams/{team_id}/members` | List team members |
| `DELETE` | `/api/teams/{team_id}/members/{user_id}` | Remove team member |

### Backlog

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/backlog/teams/{team_id}/items` | Create backlog item |
| `GET` | `/api/backlog/teams/{team_id}/items` | List backlog items |
| `GET` | `/api/backlog/teams/{team_id}/items/{item_id}` | Get backlog item |
| `PUT` | `/api/backlog/teams/{team_id}/items/{item_id}` | Update backlog item |
| `PATCH` | `/api/backlog/teams/{team_id}/items/{item_id}/status` | Move item status |
| `PATCH` | `/api/backlog/teams/{team_id}/items/{item_id}/sprint` | Assign or unassign sprint |
| `POST` | `/api/backlog/teams/{team_id}/reorder` | Reprioritise items |
| `DELETE` | `/api/backlog/teams/{team_id}/items/{item_id}` | Delete backlog item |

### Sprints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/sprints/teams/{team_id}/sprints` | Create sprint |
| `GET` | `/api/sprints/teams/{team_id}/sprints` | List team sprints |
| `GET` | `/api/sprints/teams/{team_id}/sprints/{sprint_id}` | Get sprint with optional items |
| `PUT` | `/api/sprints/teams/{team_id}/sprints/{sprint_id}` | Update sprint |
| `DELETE` | `/api/sprints/teams/{team_id}/sprints/{sprint_id}` | Delete sprint |

## Testing

Run tests locally:

```bash
uv run pytest
```

Run specific suites:

```bash
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

With Docker:

```bash
make test
make test-unit
make test-integration
```

## Design Notes

### Why `asyncpg`

I used `asyncpg` instead of a full ORM to keep the API small and explicit. This makes authorization checks and team-scoped SQL easy to inspect during review. It also avoids hiding important multi-tenant filters behind ORM abstractions.

### Team isolation

Team membership is the core authorization boundary. Protected services call membership checks before accessing team-owned data. Repository queries also scope backlog and sprint records by `team_id`, so item access requires both a valid item id and the correct team context.

### Authentication model

The API stores users in its own `users` table and hashes passwords with Argon2. Login returns a signed JWT containing the user id in the `sub` claim. Protected routes use `Authorization: Bearer <token>`.

### Ordering model

Each backlog item has a numeric `priority_rank`. New items are spaced by `1000`, and the reorder endpoint can update explicit ranks in bulk. Lower ranks appear first.

### Workflow model

Status changes are intentionally separate from general item updates. This keeps workflow rules in one service method and prevents arbitrary status jumps.

Current statuses:

- `backlog`
- `todo`
- `in_progress`
- `review`
- `done`

### Scope deliberately kept small

I focused on the API contract, team isolation, validation, and reproducible setup. I did not build a UI, advanced sprint analytics, invitation emails, role-permission granularity beyond admin/member, or a full migration framework because they are outside the core exercise.

## Production Next Steps

If this API were moving toward production, I would add:

- **Database migrations**: introduce Alembic or another versioned migration workflow instead of a single SQL bootstrap file.
- **Stronger authorization**: expand role permissions for admin/member behavior and add invitation flows.
- **Refresh tokens**: support shorter-lived access tokens with refresh token rotation.
- **Row-level security**: evaluate Supabase RLS as an additional database-side safety boundary.
- **Observability**: add structured logging, request IDs, metrics, tracing, and alerting.
- **Rate limiting**: protect auth endpoints from brute-force attempts.
- **CI/CD**: run linting, type checks, tests, and migration checks on every pull request.
- **Pagination consistency**: consider cursor pagination for larger backlogs.
- **Error format standardization**: wrap errors in a consistent response envelope with application-specific error codes.

## Demo Checklist

1. Open `/docs`.
2. Register and login.
3. Create a team.
4. Create two backlog items.
5. List items with pagination/filtering.
6. Move an item from `backlog` to `todo` to `in_progress`.
7. Reorder one item.
8. Create a sprint and assign an item to it.
9. Show sprint details with items.
10. Login as a second user and show `403 Forbidden` on the first team's backlog.

## Author

Than Myo Htet

- GitHub: [YoutLone](https://github.com/YoutLone)

## License

This project is licensed under the MIT License. See `LICENSE` for details.
