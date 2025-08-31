# Meeting Actions

A minimal web app that extracts **Decisions** and **Action Items** from meeting transcripts using **Gemini 2.5** and syncs them to **Notion** databases.

## Features

- 📝 Paste meeting transcripts and extract structured data
- 🤖 AI-powered analysis using Google's Gemini 2.5 models
- 📋 Extract decisions with owners, rationale, and effective dates
- ✅ Extract action items with assignees, due dates, and priorities
- 🔄 Idempotent Notion sync (no duplicates)
- 🎨 Clean, modern web interface
- 🐳 Docker ready

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Google AI API key
- Notion integration token and database IDs

### 2. Setup

```bash
# Clone and enter directory
cd meeting-actions

# Copy environment template
cp env.example .env

# Edit .env with your credentials
GOOGLE_API_KEY=your_google_api_key
NOTION_TOKEN=secret_your_notion_token
NOTION_BACKLOG_DB=your_backlog_database_id
NOTION_DECISIONS_DB=your_decisions_database_id
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The app will be available at `http://localhost:8000`

### 5. Using Docker

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

## Notion Database Setup

### Backlog Database Properties:
- **Name** (Title)
- **Status** (Select: Todo, In Progress, Done)
- **Priority** (Select: P0, P1, P2)
- **Due** (Date)
- **Notes** (Rich Text)
- **Source** (URL)
- **External ID** (Rich Text)

### Decisions Database Properties:
- **Name** (Title)
- **Owner** (Rich Text)
- **Rationale** (Rich Text)
- **Effective Date** (Date)
- **Source** (URL)
- **External ID** (Rich Text)

## Usage

1. **Paste Transcript**: Copy your meeting transcript into the text area
2. **Configure Analysis**: Enter team name, product, and meeting date
3. **Analyze**: Click "Analyze Meeting" to extract decisions and actions
4. **Review Results**: Use tabs to review extracted decisions and action items
5. **Sync to Notion**: Optionally add meeting URL and sync to Notion databases

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
