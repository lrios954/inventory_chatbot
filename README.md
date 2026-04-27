# Cars Inventory API

This project is split into separate services so each part has one clear job.

The **inventory API service** is the system of record. It owns the car inventory
CRUD endpoints, the database model, validation rules, and all direct PostgreSQL
access. Any client that needs inventory data should go through this API instead
of reading the database directly.

The **chatbot service** is a separate FastAPI server for non-technical users. It
does not own inventory data and does not talk to PostgreSQL. Instead, it runs a
Strands Agent backed by Amazon Bedrock Claude Haiku.

Between the chatbot agent and the inventory API there is a **local MCP server**
inside `chatbot_app`. The MCP server exposes a small set of read-only inventory
tools, such as searching cars, looking up a VIN, and summarizing inventory. This
keeps the agent focused on asking for business capabilities while the inventory
API remains responsible for the actual data and behavior.

```text
User / Postman
  -> Chatbot API service on :8001
  -> Strands Agent using Bedrock Claude Haiku
  -> local MCP server with inventory tools
  -> Inventory API service on :8000
  -> PostgreSQL
```

This separation keeps the CRUD API reusable, keeps the chat workflow isolated,
and makes the MCP tools a controlled boundary between natural-language requests
and inventory operations.

## Run With Docker

Create a `.env` file if you want to use the chatbot:

```bash
cp .env.example .env
```

Then configure AWS credentials with access to Amazon Bedrock. For local Docker
development with temporary credentials, set these values in `.env`:

```text
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
```

Do not set `AWS_BEARER_TOKEN_BEDROCK` when using temporary AWS session
credentials.

```bash
docker compose up --build
```

The API will be available at:

- Inventory API: <http://localhost:8000>
- Inventory Swagger UI: <http://localhost:8000/docs>
- Inventory health check: <http://localhost:8000/health>
- Chatbot API: <http://localhost:8001>
- Chatbot Swagger UI: <http://localhost:8001/docs>
- Chatbot health check: <http://localhost:8001/health>

## Car Endpoints

```text
POST   /cars
GET    /cars
GET    /cars/vin/{vin}
GET    /cars/{car_id}
PATCH  /cars/{car_id}
DELETE /cars/{car_id}
```

Example payload:

```json
{
  "vin": "1HGCM82633A004352",
  "make": "Toyota",
  "model": "Corolla",
  "year": 2024,
  "color": "Silver",
  "mileage": 12500,
  "price": 21999.99,
  "status": "available",
  "location": "Main lot"
}
```

## Chatbot Endpoint

The chatbot runs as a separate FastAPI service in `chatbot_app`. It uses a
Strands Agent with Amazon Bedrock Claude Haiku and a local MCP server:

```text
POST /chat
  -> Strands Agent using Bedrock Claude Haiku
  -> local MCP server: chatbot_app.mcp_server
  -> inventory API: http://api:8000
  -> PostgreSQL
```

```text
POST /chat
```

Example request:

```json
{
  "message": "Show me available Toyota cars under $25,000."
}
```

The chatbot service is read-only. It can search and summarize inventory, but it
cannot create, update, reserve, sell, or delete cars.

The local MCP server exposes these inventory tools to the Strands Agent:

```text
inventory_health
list_cars
get_car_by_id
get_car_by_vin
search_cars
get_inventory_summary
```

### Test The Chatbot With Postman

Check chatbot health:

```text
GET http://localhost:8001/health
```

Ask the chatbot a question:

```text
POST http://localhost:8001/chat
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "message": "Do we have any available Hondas under $25,000?"
}
```

If AWS credentials or Bedrock model access are missing, the chatbot returns a
`502` error with the Bedrock failure details.

## Local Development Without Docker API Container

Start only PostgreSQL:

```bash
docker compose up db
```

Create a virtual environment, install dependencies, and run the API:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Run the chatbot service locally in another terminal:

```bash
cd chatbot_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
INVENTORY_API_URL=http://localhost:8000 uvicorn chatbot_app.main:app --reload --port 8001
```

You can inspect the local MCP server separately with an MCP inspector or by
running it directly:

```bash
INVENTORY_API_URL=http://localhost:8000 python -m chatbot_app.mcp_server
```
