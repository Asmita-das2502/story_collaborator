# 📖 Story Collaborator

### A collaborative story writing tool powered by Cognee's persistent memory

> Two authors. One story. An AI that never forgets.

---

## 🌟 The Problem

My friend and I are co-writing a novel together — from different cities. Our entire creative process lived in WhatsApp: character discussions, plot decisions, world-building ideas, all scattered across hundreds of messages with no structure and no memory.

Every time we sat down to write, we'd spend the first 20 minutes just catching up:

- "Wait, what did we decide about Kira's backstory?"
- "Did we ever resolve the Lord Vael plotline?"
- "What was the tone we were going for again?"

There was no agent, no tool, no system that could **remember our creative process across sessions** and help us actually write.

Story Collaborator solves this — by giving our story a persistent, graph-powered memory brain.

---

## 💡 What It Does

Story Collaborator is a real-time collaborative writing app where every conversation about your story is **remembered, connected, and made retrievable** using Cognee's knowledge graph.

### Core Features

| Feature              | What it does                                                  | Powered by                        |
| -------------------- | ------------------------------------------------------------- | --------------------------------- |
| 💬 **Chat**          | Real-time story discussion between collaborators              | FastAPI + PostgreSQL              |
| 🗺️ **Summary**       | On-demand narrative summary of your story so far              | Cognee `GRAPH_COMPLETION`         |
| 🔍 **Ask Memory**    | Freeform Q&A about your story ("what do we know about Kira?") | Cognee `GRAPH_COMPLETION`         |
| 📝 **Chapter Draft** | AI drafts a chapter using your story's graph context          | Cognee → Groq LLaMA               |
| 💡 **Suggestions**   | Plot, character, twist, and ending suggestions from the graph | Cognee `GRAPH_COMPLETION`         |
| 🧵 **Loose Ends**    | Finds unresolved plot threads and character arcs              | Cognee `GRAPH_SUMMARY_COMPLETION` |

---

## 🧠 How Cognee Powers the Memory

This is not a chatbot that stores conversation history in a list. Cognee builds a **knowledge graph** from every message — extracting entities, relationships, and concepts that persist across sessions.

### The Memory Pipeline

```
User sends message
       ↓
Save to PostgreSQL (raw log, always reliable)
       ↓
cognee.add(formatted_message, dataset_name=story_room_id)
       ↓
cognee.cognify() → LLM extracts entities + relationships → builds graph
       ↓
Graph nodes: Characters, Plot Points, Conflicts, Themes, Settings
Graph edges: "is a warrior", "knows about", "is set in", "conflicts with"
```

### Why Graph Memory, Not Vector Search?

A plain vector store would let you search for _similar text_. Cognee's graph lets you traverse _relationships_:

- **Vector search:** "Find messages similar to 'Kira lost her memory'"
- **Graph traversal:** "Kira → lost memory → mysterious battle → Lord Vael knows why → political conspiracy → unresolved thread"

When you ask "what should happen in Chapter 3?", the agent doesn't just find similar sentences — it follows the graph: character → open arc → thematic thread → suggested direction. That's the difference.

### Dataset Scoping

Every story room has its own isolated Cognee dataset (`story_room_{room_id}`), so multiple stories never bleed into each other's graph.

### Search Types Used

| Feature                          | SearchType                     | Why                                                              |
| -------------------------------- | ------------------------------ | ---------------------------------------------------------------- |
| Summary, Ask Memory, Suggestions | `GRAPH_COMPLETION`             | Full graph traversal with LLM reasoning — best for narrative Q&A |
| Chapter Context                  | `GRAPH_COMPLETION` × 3 queries | Separate queries for characters, plot, tone — structured context |
| Loose Ends                       | `GRAPH_SUMMARY_COMPLETION`     | Pattern detection across the whole graph — finds what's missing  |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser UI                     │
│  Chat │ Summary │ Suggestions │ Chapters │ More  │
└──────────────────────┬──────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend                     │
│  /api/messages  /api/summary  /api/suggestions   │
│  /api/threads   /api/draft-chapter  /api/recall  │
└──────┬───────────────────────────────┬──────────┘
       │                               │
┌──────▼──────┐                ┌───────▼────────┐
│  PostgreSQL  │                │  Cognee Memory  │
│  (raw data)  │                │  Knowledge Graph│
│  Users       │                │  + Vector Store │
│  Rooms       │                │  (LanceDB/Kuzu) │
│  Messages    │                │                 │
│  Chapters    │                │  LLM: Groq      │
└─────────────┘                │  Embeddings:    │
                                │  Fastembed      │
                                └────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/story-collaborator.git
cd story-collaborator
```

**2. Create virtual environment**

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows (Git Bash)
# or
source .venv/bin/activate       # macOS/Linux
```

**3. Install dependencies**

```bash
pip install cognee fastembed fastapi uvicorn psycopg2-binary python-dotenv asyncpg sqlalchemy groq
```

**4. Start PostgreSQL**

```bash
docker compose up -d
```

**5. Configure environment**

Create a `.env` file in the project root:

```env
# LLM (via Groq)
LLM_PROVIDER=custom
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_API_KEY=your_groq_api_key_here

# Embeddings (local, no API key needed)
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
EMBEDDING_MAX_TOKENS=256

# Cognee storage (keep paths short on Windows)
DATA_ROOT_DIRECTORY="C:/cognee-proj/.cognee_data"
SYSTEM_ROOT_DIRECTORY="C:/cognee-proj/.cognee_system"

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/story_collaborator_db
```

**6. Run the app**

```bash
uvicorn app.main:app --reload
```

**7. Open in browser**

```
http://localhost:8000
```

---

## 📱 Usage

1. **Enter your name** and a story room name on the setup screen
2. **Send messages** discussing your story — characters, plot, world-building
3. Each message is automatically **ingested into Cognee's graph** (you'll see ✓ remembered)
4. Use the sidebar to:
   - **🗺️ Summary** — get a full narrative summary of your story so far
   - **🔍 Ask Memory** — ask anything ("what do we know about Kira?")
   - **💡 Suggestions** — get plot/character/twist/ending ideas from your graph
   - **📝 Chapters** — draft a chapter using your story's memory as context
   - **🧵 Loose Ends** — find unresolved threads and unanswered questions

Your friend can join the **same room name** from any device and share the same memory graph.

---

## 🗂️ Project Structure

```
story-collaborator/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── database.py          # SQLAlchemy async engine
│   ├── models.py            # DB models: User, StoryRoom, Message, Chapter
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routers/
│   │   ├── chat.py          # Chat, users, rooms, recall endpoints
│   │   ├── summary.py       # Summary, suggestions, threads endpoints
│   │   └── chapters.py      # Chapter draft and save endpoints
│   └── memory/
│       └── cognee_client.py # All Cognee operations (single source of truth)
├── static/
│   ├── index.html           # Single-page app UI
│   ├── style.css            # Dark theme styling
│   └── app.js               # Frontend logic
├── docker-compose.yml       # PostgreSQL container
├── .env                     # Environment variables (not committed)
└── README.md
```

---

## 🛠️ Tech Stack

| Layer        | Technology                                                           |
| ------------ | -------------------------------------------------------------------- |
| Memory       | [Cognee](https://github.com/topoteretes/cognee) v1.2.2 (open-source) |
| LLM          | Groq LLaMA 3.3 70B                                                   |
| Embeddings   | Fastembed (local, sentence-transformers/all-MiniLM-L6-v2)            |
| Backend      | FastAPI + SQLAlchemy (async)                                         |
| Database     | PostgreSQL (Docker)                                                  |
| Graph Store  | Kuzu (via Cognee)                                                    |
| Vector Store | LanceDB (via Cognee)                                                 |
| Frontend     | Vanilla HTML/CSS/JavaScript                                          |

---

## 🎯 Hackathon Track

**WeMakeDevs × Cognee Hackathon — Best Use of Open Source Track**

Built on Cognee open-source library v1.2.2. The memory architecture uses Cognee's full ECL (Extract → Cognify → Load) pipeline with graph-vector hybrid retrieval.

### Why this project pushes Cognee's boundaries

Most memory applications use Cognee as a "smarter vector store" — add text, search for similar text. Story Collaborator uses the **graph layer** as a first-class citizen:

- Entity extraction from conversational text ("Kira said: ...") into structured character/plot/theme nodes
- Cross-session relationship traversal ("what connects Kira to the political conspiracy?")
- Pattern detection across the full graph for unresolved narrative threads
- Multi-query context assembly for chapter generation (3 separate graph queries per draft)

---

## 🔮 What's Next

- **Real-time sync** between collaborators using WebSockets
- **Export to PDF/EPUB** - turn your drafted chapters into a readable document
- **Timeline view** - visualize your story's plot graph visually
- **cognee.improve()** - feed author feedbadk on chapter drafts back into the memory graph so the agent learns your preferences and writing style over time.
- **cognee.forget()** -let authors surgically remove plot decisions they've abandoned,keeping the graph clean and relevant as the story evolves.
- **Room authentication** - password-protect story rooms so only invited collaborators can access a room's content and memory graph. Right now rooms are identified by name only, which is fine for private use but not for sharing over a public deployment
- **Invite system** - share a room via a unique invite link rather than just a room name, so your co-author can join securely without guessing the room name

---

## 👩‍💻 Built by

Asmita Das — B.Tech Computer Science, ICFAI University Tripura

_"I built this because my friend and I needed it."_

---

## 🤖 AI Tools

This project was built faster and more efficiently with the assistance of AI engineering tools ( ex- claude).
