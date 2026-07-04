# 📖 Story Collaborator

### A collaborative story writing tool powered by Cognee's persistent memory

> Two authors. One story. An AI that never forgets.

---

## The Problem

My friend and I are co-writing a novel from different cities. Our entire creative process lived in WhatsApp, hundreds of messages with no memory and structure. Every wrting session started with 20 minutes of catching up on what we'd already decided.

Story Collaborator fixes this by giving our story a persistent, graph-powered memory using Cognee.

---

## What It Does

| Feature                                                   | Powered by                        |
| --------------------------------------------------------- | --------------------------------- |
| Chat - discuss your story,every message remembered        | 'cognee.remember()'               |
| Summary - narrative summary of the story so far           | 'cognee.search()'GRAPH_COMPLETION |
| Ask Memory - freeform Q&A about the story                 | 'cognee.recall()'                 |
| Chapters - AI drafts a chapter from story context         | 'cognee.search()' X 3 quiries     |
| Finalize Chapters - approving a chapter updates the graph | 'cognee.improve()'                |
| Suggestions - plot,character,twist,ending ideas           | 'cognee.search()'GRAPH_COMPLETION |
| Loose Ends - find unresolved plot threads                 | 'cognee.search()'GRAPH_COMPLETION |
| Clear Memory- rest the graph for a story room             | 'cognee.forget()'                 |

---

## 🧠 How Cognee Powers the Memory

Every chat message is ingested into Cognee's knowledge graph:

```python

# Every message -> knowledge graph
await cognee.remember(f'{sender} said: "{content}"' , dataset_name=room_id)

#Retrieve story context
results=await cognee.recall(query,dataset_name=room_id)

#Reinforce graph when chapter is approved
await cognee.improve(chapter_content,dataset_name=room_id)

#Reset graph if story direction changes
await cognee.forget(dataset_name=room_id)

```

Each story room has its won isolated Cognee dataset - multipel stories never bleed into each other.

The graph doesn't just store text -it extracts entities and their relationships, so when you ask "what connects kira to lord vael? it traverses the graph , not just finds similar sentences.

## Stack

-**Memory:** Cognee v1.2.2(open-source) -**LLM:** Groq LLaMA 3.3 70B -**Embeddings:** Fastembed -**Backend:** FastAPI + SQLAIchemy async -**Database:** PostgreSQL -**Frontend:** Vanilla HTML/CSS/ JavaScript

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

LLM_PROVIDER=custom
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_API_KEY=your_groq_api_key_here

# Embeddings (local, no API key needed)
EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS=384
EMBEDDING_MAX_TOKENS=256

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

## Tech Stack

---

## What's Next

- **Room authentication** - password-protect story rooms so only invited collaborators can access a room's content and memory graph. Right now rooms are identified by name only, which is fine for private use but not for sharing over a public deployment
- **Invite system** - share a room via a unique invite link rather than just a room name, so your co-author can join securely without guessing the room name

---

## AI Tools

This project was built faster and more efficiently with the assistance of AI engineering tools ( ex- claude).
