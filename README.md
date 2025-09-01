# Meeting Actions

A minimal web app that extracts **Decisions** and **Action Items** from meeting transcripts using **Gemini 2.5** and syncs them to **Notion** databases.

## Features

- 🎤 Upload audio/video recordings and auto-transcribe using Gemini
- 📝 Paste meeting transcripts and extract structured data
- 🤖 AI-powered analysis using Google's Gemini 2.5 models
- 📋 Extract decisions with owners, rationale, and effective dates
- ✅ Extract action items with assignees, due dates, and priorities
- 🔄 Idempotent Notion sync (no duplicates)
- 🎨 Clean, modern web interface
- 🐳 Docker ready

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Google AI API key ([Get one here](https://aistudio.google.com/app/apikey)) - Used for both transcription and analysis
- Notion integration token and database IDs ([Setup guide below](#notion-setup))

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd meeting-actions

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env with your credentials
GOOGLE_API_KEY=your_google_api_key
NOTION_TOKEN=secret_your_notion_token
NOTION_BACKLOG_DB=your_backlog_database_id
NOTION_DECISIONS_DB=your_decisions_database_id
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Run the Application

```bash
python app.py
```

The app will be available at `http://localhost:8000`

### 4. Using Docker

```bash
# Build the image
docker build -t meeting-actions .

# Run with environment file
docker run -p 8000:8000 --env-file .env meeting-actions
```

## API Endpoints

### `POST /ingest`
Ingest a meeting transcript.
- **Body**: `transcript` (form data)
- **Returns**: `{"transcript_id": "uuid"}`

### `POST /analyze`
Analyze transcript to extract decisions and actions.
- **Query params**: 
  - `transcript_id`: UUID from ingest
  - `team`: Team name
  - `product`: Product name  
  - `date`: Meeting date (YYYY-MM-DD)
- **Returns**: Analysis JSON with decisions and actions

### `POST /notion/sync`
Sync analysis results to Notion databases.
- **Body**: `{"analysis": {...}, "meeting_url": "optional"}`
- **Returns**: Sync results with created/updated counts

### `GET /healthz`
Health check endpoint.
- **Returns**: `{"ok": true}`

## Notion Setup

### Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "Meeting Actions")
4. Select your workspace
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `secret_`)

### Step 2: Create Databases

Create two databases in Notion with these exact properties:

#### **Backlog Database** (for Action Items):
- **Name** (Title) - Required
- **Status** (Select) - Options: Todo, In Progress, Done
- **Priority** (Select) - Options: P0, P1, P2  
- **Due** (Date)
- **Notes** (Rich Text)
- **Source** (URL)
- **External ID** (Rich Text) - Required

#### **Decisions Database**:
- **Name** (Title) - Required
- **Owner** (Rich Text)
- **Rationale** (Rich Text)
- **Effective Date** (Date)
- **Source** (URL)
- **External ID** (Rich Text) - Required

### Step 3: Share Databases with Integration

1. Open each database
2. Click **"Share"** (top right)
3. Add your integration
4. Give it **"Edit"** permissions
5. Click **"Invite"**

### Step 4: Get Database IDs

1. Open each database in Notion
2. Copy the URL - it looks like: `https://notion.so/workspace/DATABASE_ID?v=...`
3. Extract the 32-character DATABASE_ID (remove dashes)
4. Add to your `.env` file

## Usage

1. **Upload Recording**: Drag & drop or select an audio/video file (MP3, MP4, WAV, etc.)
2. **Or Paste Transcript**: Alternatively, paste your meeting transcript into the text area
3. **Configure Analysis**: Enter team name, product, and meeting date
4. **Analyze**: Click "Analyze Meeting" to extract decisions and actions
5. **Review Results**: Use tabs to review extracted decisions and action items
6. **Sync to Notion**: Optionally add meeting URL and sync to Notion databases

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key | Required |
| `NOTION_TOKEN` | Notion integration token | Required |
| `NOTION_BACKLOG_DB` | Notion backlog database ID | Required |
| `NOTION_DECISIONS_DB` | Notion decisions database ID | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |

## Features

- **Idempotent Sync**: Uses SHA256 hash of meeting URL + title to prevent duplicates
- **Flexible Models**: Switch between `gemini-2.5-flash` (fast) and `gemini-2.5-pro` (deep)
- **Error Handling**: Graceful error handling with user-friendly messages
- **Modern UI**: Responsive design with smooth animations
- **Production Ready**: Docker support, health checks, proper error handling

## Architecture

```
meeting-actions/
├── app.py              # FastAPI application and routes
├── llm.py              # Gemini AI integration
├── models.py           # Pydantic data models
├── notion_sync.py      # Notion database synchronization
├── static/             # Frontend assets
│   ├── index.html      # Main UI
│   ├── app.js          # Frontend JavaScript
│   └── style.css       # Styling
├── requirements.txt    # Python dependencies
├── env.example         # Environment template
├── Dockerfile          # Container configuration
└── README.md          # This file
```

## License

MIT License - feel free to use for any purpose.
