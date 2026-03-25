# DeggBi AI - Copilot Instructions

## Project Overview
DeggBi AI is a deepfake detection platform for African francophone users, accessible via WhatsApp, Telegram, and web dashboard. It analyzes text, images, audio, and video content using AI models to detect misinformation, scams, and synthetic media.

## Architecture Patterns

### Async-First Design
- **All FastAPI routes are `async def`** - never use synchronous routes
- **AI analysis via Celery tasks** - heavy ML inference runs asynchronously, not in webhooks
- **Immediate webhook responses** - acknowledge receipt in <5s, send results via follow-up messages

### Dual Analysis Pipeline
```python
# Score calculation from app/core/scoring.py
score_final = (score_truthscan * 0.5) + (score_deepshield * 0.5)

# Verdicts by threshold
0-30: CONTENU FIABLE (✅)
31-60: CONTENU DOUTEUX (⚠️)
61-85: PROBABLEMENT FAUX (🔴)
86-100: DEEPFAKE CONFIRMÉ (🚨) or ARNAQUE CONFIRMÉE (🚫)
```

### Content Type Routing
- **Text**: NLP analysis + fact-checking + RAG
- **Image**: EfficientNet deepfake detection + OCR + reverse image search
- **Audio**: Whisper STT + Wav2Vec2 voice cloning detection
- **Video**: Frame extraction + combined image/audio analysis

## Development Workflow

### Local Development Setup
```bash
# Backend (Python 3.11+)
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal)
celery -A app.tasks.analysis worker --loglevel=info --concurrency=2

# Frontend (separate terminal)
cd frontend && npm run dev
```

### Testing Commands
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Database Setup
```bash
# Initialize Supabase schema
psql $DATABASE_URL -f scripts/setup_supabase.sql
```

## Code Patterns & Conventions

### Configuration Management
```python
# app/config.py - Always use this pattern
from app.config import settings  # Never import os.environ directly
```

### Database Operations
```python
# app/models/database.py - Always use Supabase client
from app.models.database import supabase

# Never use psycopg2 directly - always go through supabase-py
result = supabase.table("analyses").insert(data).execute()
```

### Error Handling
```python
# Graceful AI service degradation
try:
    result = await huggingface_api_call()
except Exception as e:
    logger.warning("HuggingFace timeout", error=str(e))
    return partial_score_with_fallback()
```

### Model Definitions
```python
# app/models/analysis.py - All data structures use Pydantic v2
class AnalysisRequest(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    content_type: ContentType = ContentType.UNKNOWN
```

### Logging
```python
# app/logging_config.py - Use structlog everywhere
import structlog
logger = structlog.get_logger()

logger.info("Analysis started", content_type="image", sender_id="123")
```

## Key Files & Directories

### Core Logic
- `app/core/scoring.py` - Score calculation and verdict logic
- `app/core/config.py` - Content type detection (missing from current structure)
- `app/tasks/analysis.py` - Main Celery task orchestrating analysis pipeline

### Services
- `app/services/truthscan.py` - NLP, OCR, STT, fact-checking
- `app/services/deepshield.py` - Image/audio deepfake detection
- `app/services/reporter.py` - Multilingual report generation

### API Integration
- `app/api/whatsapp.py` - WhatsApp Business API webhook
- `app/api/telegram.py` - Telegram Bot API webhook
- `app/api/rest.py` - REST API for B2B integrations

### Data Models
- `app/models/analysis.py` - Pydantic models for requests/responses
- `app/models/database.py` - Supabase client and database helpers

### Utilities
- `app/utils/whatsapp_client.py` - Sending WhatsApp messages
- `app/utils/media.py` - Media download/upload to Supabase Storage

## External API Patterns

### HuggingFace Integration
```python
# Use inference API for hosted models
from huggingface_hub import InferenceClient
client = InferenceClient(token=settings.huggingface_api_key)

# For local models, use transformers pipeline
from transformers import pipeline
classifier = pipeline("text-classification", model="model_name")
```

### WhatsApp API
```python
# Always respond within 5 seconds
# Send analysis results as follow-up messages
await send_whatsapp_message(
    phone_id=settings.whatsapp_phone_id,
    token=settings.whatsapp_token,
    to=sender_id,
    message=report_text
)
```

### Supabase Operations
```python
# Vector search for RAG
supabase.rpc("match_embeddings", {
    "query_embedding": embedding,
    "match_threshold": 0.8,
    "match_count": 5
}).execute()
```

## Testing Patterns

### Unit Test Structure
```python
# tests/test_scoring.py - Pure function testing
def test_compute_score_final_balanced():
    assert compute_score_final(80, 60) == 70.0

# Mock external APIs
@patch('app.services.deepshield.huggingface_api_call')
def test_deepfake_detection_with_mock(mock_api):
    mock_api.return_value = {"score": 95.0}
    result = analyze_deepshield(image_bytes)
    assert result.score == 95.0
```

### Demo Scenarios
- **Audio deepfake**: Voice cloning detection (94/100 score)
- **Manipulated image**: Flood photo misattributed (78/100 score)
- **Text scam**: Mobile money fraud (88/100 score)

## Deployment & Infrastructure

### Render.com Setup
- **Web Service**: FastAPI app with health checks
- **Worker**: Celery analysis tasks
- **Environment Variables**: All secrets injected via Render dashboard

### Production Considerations
- Redis for Celery broker/backend
- Supabase PostgreSQL with pgvector extension
- Supabase Storage for media files
- CORS configured for frontend domain

## Common Pitfalls

### Don't:
- Call AI models synchronously in webhook endpoints
- Use `os.environ` directly - always use `settings`
- Return psycopg2 connections - use supabase-py client
- Forget to handle API timeouts with fallbacks
- Mix sync/async code inappropriately

### Always:
- Add structlog logging to new functions
- Write tests for new services
- Use Pydantic models for all data structures
- Handle multilingual content (FR/EN/WO)
- Validate content types before analysis