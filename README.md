# J.A.R.V.I.S. AI Assistant

> *Just A Rather Very Intelligent System*

A full-stack Iron Man JARVIS AI assistant with real-time voice control, computer vision, smart home integration, multi-agent task orchestration, and a cyberpunk HUD interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ┌──────────┐┌──────────┐┌──────────┐┌───────────────────┐  │
│  │ ChatPanel ││VisionPanel││SmartHome ││ IronLegionPanel   │  │
│  └──────────┘└──────────┘└──────────┘└───────────────────┘  │
│  ┌──────────┐┌──────────┐┌──────────┐┌───────────────────┐  │
│  │VoiceOutput││NotesPanel││ Files    ││ SearchResultsCard │  │
│  └──────────┘└──────────┘└──────────┘└───────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │    WebSocket (live stats, real-time updates)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP + WebSocket (port 8000)
┌──────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────┐┌──────────┐┌──────────┐┌───────────────────┐  │
│  │  ai.py   ││ vision   ││ system   ││  smarthome        │  │
│  │ (Groq/   ││ (YOLOv8, ││ control  ││  (Home Assistant  │  │
│  │  Gemini) ││  face)   ││ (files,  ││   Hue, Kasa)      │  │
│  └──────────┘└──────────┘└──────────┘└───────────────────┘  │
│  ┌──────────┐┌──────────┐┌──────────┐┌───────────────────┐  │
│  │ legion   ││ search   ││ memory   ││  telegram_bot     │  │
│  │ (multi-  ││ (DuckDuck││ (ChromaDB││  (Telegram        │  │
│  │  agent)  ││  Go,     ││  vector  ││   integration)    │  │
│  │          ││  extract)││  memory) ││                   │  │
│  └──────────┘└──────────┘└──────────┘└───────────────────┘  │
│  ┌──────────┐┌──────────┐┌──────────┐┌───────────────────┐  │
│  │ voice    ││ memory   ││ scheduler││  cache (Redis)    │  │
│  │ (gTTS,   ││ (SQLite  ││ (remind- ││  (response        │  │
│  │  STT)    ││  convos) ││  ers)    ││   caching)        │  │
│  └──────────┘└──────────┘└──────────┘└───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### AI & Conversation
- **Groq** `llama-3.3-70b-versatile` (primary) + **Gemini** `gemini-2.0-flash` (fallback)
- Real-time token streaming over WebSocket + SSE
- Semantic vector memory via **ChromaDB** — recalls past conversations contextually
- Iron Legion multi-agent task decomposition (async concurrent dispatch)

### Voice
- **Always-on voice mode** — Web Speech API single-shot + auto-restart
- Speech-to-text via Web Speech API / SpeechRecognition
- Text-to-speech via gTTS with British voice
- Real-time waveform animation

### Vision
- Face registration and identification (`face_recognition`)
- YOLOv8n real-time object detection
- Gemini Vision scene analysis with weapon threat detection
- Screen capture and description

### System Control
- CPU (per-core), RAM, swap, disk, battery, GPU, network stats
- Cross-platform app launcher (20+ apps)
- File CRUD with filename search
- AST-safety-filtered code execution sandbox
- Screenshot capture

### Smart Home
- **Home Assistant** REST API (primary)
- **Philips Hue** local API (fallback)
- **Kasa** smart plugs (fallback)
- Device control (lights, switches, sensors, climate)

### Research & Search
- DuckDuckGo web/image/news/video search
- 3-level deep research pipeline (quick/standard/deep)
- Full page content extraction (readability + newspaper3k)

### Telegram Bot
- Chat with JARVIS from anywhere
- Commands: `/weather`, `/news`, `/search`, `/stats`
- Voice message transcription
- Runs as a daemon thread alongside FastAPI

### Cache (Redis)
- Response caching for weather, news, system stats
- AI response deduplication (10-min TTL)
- Pre-fetch warmup on server start

### Notes
- Full CRUD with search and tags
- SQLite persistent storage

## Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.14+, FastAPI, Uvicorn |
| **Frontend** | React 19, Vite 5 (JSX, no TypeScript) |
| **AI** | Groq SDK, Google Generative AI SDK |
| **Vector DB** | ChromaDB (all-MiniLM-L6-v2) |
| **Cache** | Redis (optional, graceful fallback) |
| **Database** | SQLite (conversations, notes, reminders) |
| **Vision** | OpenCV, face_recognition, Ultralytics YOLOv8 |
| **Voice** | Web Speech API, gTTS, SpeechRecognition |
| **Smart Home** | Home Assistant API, Philips Hue, Kasa |
| **Search** | duckduckgo_search, readability, newspaper3k |

## Setup

### Prerequisites
- Python 3.14+
- Node.js 20+
- Groq API key (free at console.groq.com)
- Google Gemini API key (free at aistudio.google.com)

### Installation

```bash
# Clone
git clone https://github.com/trivedivatsal63-stack/Jarvis.git
cd Jarvis

# Backend
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Configuration

Create `backend/.env`:

```env
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=AIza_your_key_here
WEATHER_API_KEY=your_key        # openweathermap.org (free)
NEWS_API_KEY=your_key           # newsapi.org (free)
TELEGRAM_BOT_TOKEN=your_token   # from @BotFather (optional)
REDIS_URL=                      # optional (leave empty to skip)
```

### Run

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## API Endpoints

### Chat
- `POST /chat` — Stream AI response (SSE)
- `POST /chat/reset` — Clear conversation history

### Memory (ChromaDB)
- `POST /memory/query?query=...` — Semantic search
- `GET /memory/count` — Stored memories count

### System
- `GET /system` — CPU, RAM, disk, battery stats
- `GET /system/stats` — Detailed system stats
- `GET /system/apps` — Available applications

### Files
- `GET /files/list?path=...`
- `GET /files/read?path=...`
- `POST /files/create?path=...`
- `GET /files/search?query=...`
- `DELETE /files/delete?path=...`

### Smart Home
- `GET /home/devices` — List devices
- `POST /home/control` — Control device
- `GET /home/status` — Status summary

### Vision
- `POST /vision/register` — Register face
- `POST /vision/identify` — Identify faces
- `POST /vision/scan` — Detect objects + threats
- `POST /vision/analyze` — Gemini scene analysis

### Search
- `GET /search?q=...` — Web search
- `GET /search/images?q=...` — Image search
- `GET /search/news?q=...` — News search
- `POST /research` — Deep research

### Telegram
- `GET /cache/status` — Redis cache status
- `POST /cache/clear` — Clear cache

### WebSocket
- `ws://localhost:8000/ws` — Real-time stats, streaming, reminders

### Health
- `GET /health` — All module statuses

## Deployment

### Railway (recommended for MVP)
1. Push to GitHub
2. Create a Railway project from the repo
3. Add a **Redis** plugin
4. Set environment variables in Railway dashboard
5. Deploy — Railway auto-detects `requirements.txt`

### What runs where:
| Component | Port | Service |
|-----------|------|---------|
| Backend (FastAPI) | 8000 | Railway web service |
| Frontend (Vite) | 5173 | Railway + static hosting or separate service |
| Redis | — | Railway Redis plugin |

### Frontend build for production:
```bash
cd frontend
npm run build    # outputs to frontend/dist/
```

Serve `frontend/dist/` via Railway's static hosting or a simple Express/nginx server.

## Project Structure

```
jarvis-assistant/
├── backend/
│   ├── main.py              # FastAPI app — all routes, WebSocket
│   ├── ai.py                # Groq + Gemini streaming
│   ├── tools.py             # Weather, News, Web Search, intent detection
│   ├── memory.py            # SQLite conversations, notes, reminders
│   ├── memory_vector.py     # ChromaDB semantic memory
│   ├── voice.py             # gTTS TTS, SpeechRecognition STT
│   ├── cache.py             # Redis response caching
│   ├── telegram_bot.py      # Telegram bot integration
│   ├── vision.py            # Face, YOLO, Gemini Vision
│   ├── system_control.py    # System stats, app launcher, file CRUD, code exec
│   ├── smarthome.py         # Home Assistant, Hue, Kasa
│   ├── legion.py            # Multi-agent task orchestration
│   ├── search.py            # DuckDuckGo + content extraction
│   ├── scheduler.py         # APScheduler reminders
│   ├── ws.py                # WebSocket manager
│   ├── .env                 # API keys (gitignored)
│   └── chroma_db/           # ChromaDB persistent data (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── context/
│   │   │   └── JarvisContext.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useVoice.js
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── TopNav.jsx
│   │   │   ├── VisionPanel.jsx
│   │   │   ├── SmartHomePanel.jsx
│   │   │   ├── IronLegionPanel.jsx
│   │   │   ├── VoiceOutput.jsx
│   │   │   ├── RemindersPanel.jsx
│   │   │   ├── NotesPanel.jsx
│   │   │   ├── SearchResultsCard.jsx
│   │   │   └── BootSequence.jsx
│   │   └── styles/
│   │       └── jarvis.css
│   └── vite.config.js
├── requirements.txt
├── .gitignore
└── README.md
```

## License

MIT
