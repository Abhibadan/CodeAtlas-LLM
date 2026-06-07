# 🗺️ CodeAtlas-LLM

> **AI-powered Knowledge Transfer (KT) assistant that helps developers instantly understand any codebase using Retrieval-Augmented Generation (RAG), a Knowledge Graph, and Vector Search.**

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Reference](#-api-reference)
- [How It Works](#-how-it-works)
- [Supported AI Providers](#-supported-ai-providers)

---

## 🧭 Overview

**CodeAtlas-LLM** is the AI inference backend of the CodeAtlas platform — a system designed to dramatically reduce Knowledge Transfer time when onboarding developers onto an existing codebase.

Instead of sifting through documentation and source files manually, developers can simply **ask questions in plain English** and get back precise, context-aware answers sourced directly from:

- **Codebase documentation** (vector search via ChromaDB)
- **Code dependency graph** (graph traversal via Neo4j)
- **Chat history** (conversational memory via MongoDB)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Provider AI** | Seamlessly switch between **Google Gemini**, **OpenAI**, and **Ollama** (local LLMs) |
| 🔍 **Hybrid RAG** | Combines vector similarity search + graph traversal for deep codebase understanding |
| 🧠 **Intelligent Agent** | Tool-calling agent that decides *when* to query the codebase vs. answer directly |
| 💬 **Conversation Memory** | Resolves contextual pronouns ("it", "this", "that method") using chat history |
| ⚡ **Streaming Responses** | Real-time Server-Sent Events (SSE) for token-by-token streaming |
| 📥 **Async Job Processing** | BullMQ (Redis-backed) worker queue for async vectorization of new code scans |
| 📡 **Event Broadcasting** | Kafka integration to broadcast vectorization completion events to upstream services |
| 🔐 **JWT Authentication** | Cookie-based JWT middleware to secure all API endpoints |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client / Frontend                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │  HTTP (SSE stream)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server (server.py)                  │
│   • JWT Auth Middleware                                          │
│   • POST /api/conversation                                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Agent                                │
│   • LangChain Tool-Calling Agent                                 │
│   • System prompt with smart decision tree                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │ vector_search│  │ graph_query  │  │  get_chat_history    │  │
│   │ (ChromaDB)   │  │ (Neo4j)      │  │  (MongoDB)           │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼──────────────────────┐
          ▼                     ▼                      ▼
   ┌─────────────┐      ┌─────────────┐       ┌──────────────┐
   │  ChromaDB   │      │   Neo4j     │       │   MongoDB    │
   │ (Vectors)   │      │   (Graph)   │       │  (History)   │
   └─────────────┘      └─────────────┘       └──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Background Vectorization Pipeline (vectorizer.py):

 BullMQ Job (Redis) ──► process_vectorizer_job
                              │
                     ┌────────┴─────────┐
                     ▼                  ▼
               MongoDB             ChromaDB
            (Markdowns &        (Vector Store)
            Descriptions)
                     │
                     └──► Kafka Event: vectorization_completed
```

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — High-performance async REST API framework
- **[LangChain](https://www.langchain.com/)** — LLM orchestration, agent, and tool management
- **[uvicorn](https://www.uvicorn.org/)** — ASGI server for FastAPI

### Databases
- **[ChromaDB](https://www.trychroma.com/)** — Vector database for semantic document retrieval
- **[Neo4j](https://neo4j.com/)** — Graph database for code dependency relationships
- **[MongoDB](https://www.mongodb.com/)** (via MongoEngine) — Stores projects, conversations, and user data

### Messaging & Queues
- **[BullMQ](https://bullmq.io/)** (via Python `bullmq`) — Redis-backed job queue for vectorization tasks
- **[Apache Kafka](https://kafka.apache.org/)** — Event streaming for broadcasting scan completion events
- **[Redis](https://redis.io/)** — Backing store for BullMQ

### AI Providers
- **Google Gemini** (`langchain-google-genai`)
- **OpenAI / LMStudio** (`langchain-openai`)
- **Ollama** (`langchain-ollama`, `langchain-community`)

### Auth & Security
- **PyJWT** — JWT token validation

---

## 📁 Project Structure

```
CodeAtlas-LLM/
│
├── main.py                  # Entry point — starts server + vectorizer as subprocesses, manages Kafka topics
├── server.py                # FastAPI app — defines /api/conversation SSE endpoint
├── vectorizer.py            # BullMQ worker — processes vectorization jobs and indexes code into ChromaDB
├── config.py                # Loads all env vars into typed config dicts
├── docker-compose.yml       # Spins up ChromaDB, Redis, and Kafka
├── pyproject.toml           # Poetry project metadata and dependencies
│
├── components/
│   ├── ragAgent.py          # Core RAG agent — LangChain tool-calling agent with full system prompt
│   ├── aiModelAdapter.py    # Adapter pattern — unified interface for Gemini, OpenAI, Ollama
│   ├── tools.py             # Agent tools: vector_search, graph_query, get_graph_schema, get_chat_history
│   └── __init__.py
│
├── dbModule/
│   ├── VectorDb.py          # ChromaDB client wrapper — add, retrieve, clear collections
│   ├── GraphDb.py           # Neo4j client — schema introspection, LLM-generated Cypher, query execution
│   ├── mongoDb/             # MongoEngine connection and document schemas
│   │   └── schemas/         # Project, Conversation, User, Markdown, Description models
│   └── schemas/             # Pydantic schemas for vector/graph data
│
├── kafkaService/
│   ├── kafkaAdmin.py        # Topic creation and management
│   ├── createProducer.py    # Kafka producer helpers
│   ├── createComsumer.py    # Kafka consumer helpers
│   └── topicsRegistry.py   # Enum of all Kafka topic names
│
├── bullMQ/
│   ├── conection.py         # Redis connection for BullMQ
│   ├── workerRegistry.py    # Enum of all BullMQ worker/queue names
│   └── helpers/             # WorkerLoader and related utilities
│
├── middleware/
│   └── authMiddleware.py    # Starlette middleware for JWT cookie authentication
│
├── requestDTOs/
│   └── chatDTO.py           # Pydantic DTO for the chat request body
│
└── docker-volumes/          # Persistent data volumes (gitignored)
```

---

## ✅ Prerequisites

Make sure the following are installed on your system:

- **Python 3.11+**
- **[Poetry](https://python-poetry.org/docs/#installation)** (dependency manager)
- **[Docker](https://docs.docker.com/get-docker/) & Docker Compose** (for infrastructure services)
- A running **Neo4j** instance (can be cloud or local; not included in `docker-compose.yml`)
- A running **MongoDB** instance (can be Atlas or local; not included in `docker-compose.yml`)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd CodeAtlas-LLM
```

### 2. Install Python Dependencies

```bash
# Using Poetry (recommended)
poetry install

# OR using pip
pip install -r requirements.txt
```

### 3. Start Infrastructure Services

```bash
# Starts ChromaDB, Redis, and Kafka
docker compose up -d
```

Verify services are running:

```bash
docker compose ps
```

---

## ⚙️ Configuration

Copy the `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Environment Variables

```env
# ─── MongoDB ────────────────────────────────────────────────────
MONGO_URI=mongodb://localhost:27017
MONGO_DB=codeatlas

# ─── Neo4j ──────────────────────────────────────────────────────
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# ─── ChromaDB ───────────────────────────────────────────────────
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=codeatlas

# ─── Redis (BullMQ) ─────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=          # Leave blank if no password

# ─── Kafka ──────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
KAFKA_GROUP_ID=codeatlas-llm-group

# ─── AI Provider ────────────────────────────────────────────────
# Options: gemini | openai | ollama
AI_PROVIDER=gemini

# Google Gemini
GOOGLE_API_KEY=your_google_api_key
EMBEDDING_MODEL=models/text-embedding-004
CHAT_MODEL=gemini-1.5-pro

# OpenAI / LMStudio
OPENAI_API_KEY=your_openai_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1   # or LMStudio: http://localhost:1234/v1

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2

# ─── Auth ───────────────────────────────────────────────────────
JWT_SECRET=your_jwt_secret_key
```

---

## ▶️ Running the Application

### Development (Recommended)

```bash
# Starts both server.py and vectorizer.py as managed subprocesses
# and initializes Kafka topics automatically
poetry run start

# OR directly with Python
python main.py
```

This single command will:
1. Start the **FastAPI server** on `http://0.0.0.0:4000`
2. Start the **BullMQ vectorizer worker** in the background
3. Create the `codeatlas-llm-events` Kafka topic (if it doesn't exist)

### Run Services Individually

```bash
# API server only
python server.py

# Vectorizer worker only
python vectorizer.py
```

---

## 📡 API Reference

### `POST /api/conversation`

Streams an AI response using Server-Sent Events (SSE).

**Authentication:** Requires a valid `admin_auth` JWT cookie.

**Request Body:**

```json
{
  "query": "How does the authentication module work?",
  "pid": "6651a2f3c4e5d6789abc1234",
  "cid": "6651a2f3c4e5d6789abc5678",
  "convId": "optional-conversation-id"
}
```

| Field | Type | Description |
|---|---|---|
| `query` | `string` | The user's question |
| `pid` | `string` | MongoDB ObjectId of the scanned project |
| `cid` | `string` | MongoDB ObjectId of the chat session |
| `convId` | `string` | (Optional) conversation context ID |

**Response:** `text/event-stream`

```
data: {"id": "chunk-0", "index": 0, "object": "chat.data.chunk", "delta": {"content": "The auth"}, "finish_reason": null}

data: {"id": "chunk-1", "index": 1, "object": "chat.data.chunk", "delta": {"content": " module works by..."}, "finish_reason": null}

data: {"id": "chunk-N", "index": N, "object": "chat.completion.chunk", "delta": {"content": ""}, "finish_reason": "stop"}

data: [DONE]
```

**Error Responses:**

| Status | Reason |
|---|---|
| `400` | Invalid or missing Project ID |
| `401` | Missing or invalid JWT cookie |
| `404` | Project not found in MongoDB |
| `500` | Database or streaming error |

---

## 🔬 How It Works

### 1. Query Flow (RAG Agent)

When a user sends a question, the **RAG Agent** applies a smart decision tree:

```
Is this a general programming question?
  └─ YES → Answer directly (no tools needed)
  └─ NO  → Does it have contextual references? (it, this, the method...)
               └─ YES → get_chat_history() FIRST
               └─ NO  → Is it about this specific codebase?
                            └─ YES → vector_search() → get_graph_schema() → graph_query()
                            └─ NO  → Answer directly
```

### 2. Vectorization Pipeline

When the main CodeAtlas platform scans a project:
1. It saves `Markdown` and `Description` documents to **MongoDB**
2. It enqueues a **BullMQ job** with the project ID
3. The `vectorizer.py` worker picks up the job and:
   - Fetches the documents from MongoDB
   - Embeds them using the configured AI provider
   - Stores them in **ChromaDB** (keyed by project UUID)
   - Deletes processed documents from MongoDB
   - Fires a `vectorization_completed` event to **Kafka**

### 3. Graph Queries

The agent uses the **Neo4j knowledge graph** (built by the scanner) to traverse code dependency relationships. It:
- Introspects the graph schema dynamically
- Uses the LLM to generate a valid Cypher query based on the question and vector search results
- Executes the query and formats the results for the agent context

---

## 🤖 Supported AI Providers

Configure via `AI_PROVIDER` in your `.env` file:

| Provider | Value | Notes |
|---|---|---|
| **Google Gemini** | `gemini` | Requires `GOOGLE_API_KEY` |
| **OpenAI** | `openai` | Compatible with LMStudio via `OPENAI_BASE_URL` |
| **Ollama** | `ollama` | Runs fully local — no API key needed |

Switching providers requires only a single `.env` change — no code modifications needed.

---

## 📜 License

This project was built as part of a Hackathon. See your organization's policies for usage terms.
