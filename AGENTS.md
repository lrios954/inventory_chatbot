# Project Instructions

This is a FastAPI + PostgreSQL cars inventory CRUD application.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- PostgreSQL via Docker Compose
- psycopg 3
- Separate FastAPI chatbot service in `chatbot_app`
- Strands Agents framework for chatbot agent orchestration
- Amazon Bedrock Claude Haiku as the chatbot model provider
- Local MCP server in `chatbot_app.mcp_server` for chatbot inventory tools

## Development Rules

- Keep changes small and focused.
- Prefer existing project patterns before adding new abstractions.
- Do not commit secrets or edit `.env` directly; use `.env.example` for documented config.
- Keep API behavior documented in `README.md` when endpoints change.
- Use clear HTTP status codes:
  - `201` for created resources
  - `200` for successful reads and updates
  - `204` for deletes
  - `404` when a car is not found
  - `409` for duplicate VIN conflicts

## Project Structure

- API routes live in `app/main.py` for now.
- Database models live in `app/models.py`.
- Pydantic request and response schemas live in `app/schemas.py`.
- Database CRUD helpers live in `app/crud.py`.
- Database and session setup lives in `app/database.py`.
- Chatbot API routes, Strands agent setup, and local MCP server live in `chatbot_app`.

If the API grows, split routes into `app/routers/`.

## Validation

After code changes, run:

```bash
PYTHONPYCACHEPREFIX=/tmp/project-pycache python3 -m py_compile app/*.py
PYTHONPYCACHEPREFIX=/tmp/project-pycache python3 -m py_compile chatbot_app/*.py
docker compose config
```

For API changes, also run a smoke test against Docker:

```bash
docker compose up --build -d
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## Database

- The app currently uses `Base.metadata.create_all()` for simple development.
- If schema changes become frequent, add Alembic migrations.
- VIN must remain unique.

## Chatbot

- The chatbot service must remain separate from the inventory API service.
- The chatbot service listens on port `8001`.
- The inventory API listens on port `8000`.
- The chatbot must use the Strands Agents framework.
- The chatbot must use Amazon Bedrock Claude Haiku through `BedrockModel`.
- The chatbot must access inventory through the local MCP server, not direct model function definitions.
- The local MCP server must use the inventory API as its source of truth, not direct database access.
- Keep chatbot inventory tools read-only unless the user explicitly asks for write actions.
- Do not expose AWS credentials or Bedrock API keys in code or documentation examples.

## Documentation

When adding or changing endpoints, update:

- `README.md`
- Example request bodies
- Postman testing instructions if relevant
