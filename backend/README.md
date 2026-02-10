# VaidyaAI Backend

FastAPI backend for the VaidyaAI Medical AI Platform. Provides comprehensive APIs for tutoring, study tools, clinical reasoning, and the Interactive Learning Assistant (Teach-Back Mode).

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (via Supabase)
- Virtual environment

### Setup

1. **Create virtual environment**:
```bash
python -m venv venv
```

2. **Activate virtual environment**:
- Windows: `venv\Scripts\activate`
- Unix/MacOS: `source venv/bin/activate`

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL and SUPABASE_SERVICE_KEY
# - LLM API keys (TEACH_BACK_PRIMARY_LLM_KEY, TEACH_BACK_FALLBACK_LLM_KEY)
# - LOCAL_MODELS_DIR (default: /local_models)
```

5. **Run development server**:
```bash
# Standard way
uvicorn main:app --reload

# Or with colored logging (recommended)
./start_server.sh          # Linux/macOS
start_server.bat           # Windows

# Custom port
./start_server.sh 8080
```

API available at: http://localhost:8000
API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
backend/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
│
├── config/                      # Configuration
│   ├── colored_logging.py       # Enhanced logging with colors
│   ├── model_config.py          # Model configuration
│   ├── teach_back_limits.json   # Rate limits per plan
│   └── teach_back_retention.json # Data retention policies
│
├── services/                    # Business logic services
│   ├── auth.py                  # Authentication & authorization
│   ├── chat.py                  # Chat/tutoring service
│   ├── clinical.py              # Clinical reasoning
│   ├── clinical_reasoning_engine.py  # Advanced clinical logic
│   ├── study_tools.py           # Study tools (flashcards, MCQs, etc.)
│   ├── documents.py             # Document processing & RAG
│   ├── rate_limiter.py          # Rate limiting for core features
│   ├── model_router.py          # LLM provider routing
│   ├── model_usage_logger.py    # Usage tracking
│   ├── admin.py                 # Admin operations
│   ├── audit.py                 # Audit logging
│   ├── notifications.py         # User notifications
│   ├── payments.py              # Payment processing
│   ├── scheduler.py             # Background jobs
│   ├── health_monitor.py        # Health checks
│   ├── maintenance.py           # Maintenance mode
│   ├── commands.py              # Command execution
│   ├── text_formatter.py        # Text formatting utilities
│   └── providers/               # LLM provider integrations
│       ├── openrouter.py        # OpenRouter API
│       ├── gemini.py            # Google Gemini
│       └── huggingface.py       # Hugging Face
│
├── teach_back/                  # Interactive Learning Assistant
│   ├── __init__.py
│   ├── models.py                # Pydantic data models
│   ├── session_manager.py       # Session lifecycle
│   ├── state_machine.py         # State management
│   ├── rate_limiter.py          # Independent rate limiting
│   ├── voice_processor.py       # STT/TTS integration
│   ├── llm_orchestrator.py      # Multi-role LLM coordination
│   ├── data_storage.py          # Database operations
│   ├── integrations.py          # Integration with other systems
│   ├── retention_policy.py      # Data retention & cleanup
│   ├── error_codes.py           # Error code definitions
│   ├── routes.py                # API endpoints
│   ├── admin_routes.py          # Admin controls
│   ├── README.md                # Teach-back documentation
│   └── roles/                   # AI role implementations
│       ├── student_persona.py   # Curious learner role
│       ├── evaluator.py         # Error detection role
│       ├── controller.py        # Flow control role
│       └── examiner.py          # OSCE examination role
│
├── middleware/                  # Custom middleware
│   ├── admin_auth.py            # Admin authentication
│   ├── feature_toggle.py        # Feature flag middleware
│   └── maintenance.py           # Maintenance mode middleware
│
├── database/                    # Database utilities
│   ├── COMPLETE_DATABASE_SCHEMA.sql  # Full schema
│   ├── migrations/              # Database migrations
│   └── README.md                # Database documentation
│
└── tests/                       # Test suite
    ├── conftest.py              # Pytest configuration
    ├── unit/                    # Unit tests
    ├── integration/             # Integration tests
    └── property/                # Property-based tests
```

## 🔧 Configuration

### Environment Variables

**Required**:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# LLM Configuration (Teach-Back)
TEACH_BACK_PRIMARY_LLM_PROVIDER=openrouter
TEACH_BACK_PRIMARY_LLM_MODEL=anthropic/claude-3.5-sonnet
TEACH_BACK_PRIMARY_LLM_KEY=sk-...
TEACH_BACK_FALLBACK_LLM_KEY=hf_...

# Local Models
LOCAL_MODELS_DIR=/local_models
```

**Optional**:
```bash
# Feature Flags
TEACH_BACK_ENABLED=true
TEACH_BACK_VOICE_ENABLED=true

# Integration Endpoints
FLASHCARD_SERVICE_URL=http://localhost:8000/api/flashcards
WEAK_AREA_SERVICE_URL=http://localhost:8000/api/weak-areas
STUDY_PLANNER_SERVICE_URL=http://localhost:8000/api/study-planner
MCQ_SERVICE_URL=http://localhost:8000/api/mcqs

# Logging
LOG_LEVEL=INFO
```

### Configuration Files

**`config/teach_back_limits.json`** - Rate limits per plan:
```json
{
  "free": {"sessions_per_day": 0, "voice_sessions_per_day": 0},
  "student": {"sessions_per_day": 5, "voice_sessions_per_day": 2},
  "pro": {"sessions_per_day": 20, "voice_sessions_per_day": 10},
  "admin": {}
}
```

**`config/teach_back_retention.json`** - Data retention policies:
```json
{
  "free": 7,
  "student": 30,
  "pro": 90,
  "admin": 365
}
```

## 🎨 Colored Logging

The backend features beautiful colored console output for better readability:

- **Color-coded log levels**: DEBUG (Cyan), INFO (Green), WARNING (Yellow), ERROR (Red), CRITICAL (Magenta)
- **HTTP status codes**: Automatically colored (2xx=Green, 3xx=Yellow, 4xx=Red, 5xx=Magenta)
- **Enhanced context**: Timestamps, module names, function names
- **Startup banner**: Beautiful ASCII art banner on server start

### Configuration

Colored logging is configured in `config/colored_logging.py`. Adjust log level in `main.py`:

```python
from config.colored_logging import setup_colored_logging
import logging

setup_colored_logging(level=logging.DEBUG)    # Show all logs
setup_colored_logging(level=logging.INFO)     # Default
setup_colored_logging(level=logging.WARNING)  # Only warnings+
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

**Authentication**:
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout

**Chat/Tutoring**:
- `POST /api/chat/message` - Send chat message
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat history

**Study Tools**:
- `GET /api/study-tools/flashcards` - Get flashcards
- `POST /api/study-tools/flashcards` - Create flashcard
- `GET /api/study-tools/mcqs` - Get MCQs
- `POST /api/study-tools/mcqs` - Create MCQ

**Clinical Reasoning**:
- `POST /api/clinical/case` - Get clinical case
- `POST /api/clinical/reasoning` - Get reasoning support
- `GET /api/clinical/progress` - Get progress

**Interactive Learning (Teach-Back)**:
- `POST /api/teach-back/sessions` - Create session
- `GET /api/teach-back/sessions/{id}` - Get session
- `POST /api/teach-back/sessions/{id}/input` - Process input
- `POST /api/teach-back/sessions/{id}/end` - End session
- `GET /api/teach-back/quota` - Get quota info

**Admin**:
- `GET /api/admin/users` - List users
- `POST /api/admin/feature-toggle` - Toggle features
- `GET /api/admin/usage` - Usage statistics
- `POST /api/admin/maintenance` - Maintenance mode

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories

**Unit Tests**:
```bash
pytest tests/unit/ -v
```

**Integration Tests**:
```bash
pytest tests/integration/ -v
```

**Property-Based Tests** (29 properties, 100 iterations each):
```bash
pytest tests/property/ -v
pytest tests/property/test_teach_back_properties.py -v  # Teach-back only
```

### Test Coverage
```bash
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Tests in Watch Mode
```bash
pytest-watch
```

## 🔐 Security

### Authentication
- JWT tokens via Supabase Auth
- Token validation on all protected endpoints
- Automatic token refresh

### Authorization
- Role-based access control (RBAC)
- Admin, teacher, student roles
- Feature-level permissions

### Data Protection
- End-to-end encryption for sensitive data
- Secure password hashing
- SQL injection prevention (ORM usage)
- CORS protection

### Rate Limiting
- Per-user rate limits
- Per-feature quotas
- Plan-based limits
- Admin overrides

## 📊 Monitoring

### Health Checks
```bash
curl http://localhost:8000/health
```

### Key Metrics
- Session creation/completion rates
- LLM provider performance
- Error rates by type
- User engagement metrics
- Feature usage by plan

### Logging
- Structured logging with context
- Error tracking and alerting
- Audit trail for admin actions
- Performance metrics

## 🚀 Deployment

### Docker
```bash
docker build -t vaidyaai-backend .
docker run -p 8000:8000 --env-file .env vaidyaai-backend
```

### Environment Setup
1. Set all required environment variables
2. Download local models: `bash scripts/download_teach_back_models.sh`
3. Run database migrations: `python run_migration.py`
4. Start server: `uvicorn main:app`

### Production Checklist
- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] Local models downloaded
- [ ] SSL/TLS configured
- [ ] Monitoring enabled
- [ ] Backup strategy in place
- [ ] Error tracking configured

## 📖 Additional Documentation

- **Teach-Back Module**: `teach_back/README.md`
- **Database Schema**: `database/COMPLETE_DATABASE_SCHEMA.sql`
- **Deployment Guide**: `../docs/teach_back_deployment.md`
- **Design Document**: `../.kiro/specs/medical-ai-platform/design.md`

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for changes
3. Run tests: `pytest`
4. Ensure coverage: `pytest --cov`
5. Commit with clear messages
6. Push and create PR

## 📝 Code Style

- **Python**: PEP 8 (use `black` for formatting)
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style docstrings
- **Logging**: Use structured logging

## 🐛 Troubleshooting

### Common Issues

**Port already in use**:
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

**Database connection failed**:
- Check SUPABASE_URL and SUPABASE_SERVICE_KEY
- Verify network connectivity
- Check Supabase project status

**LLM API errors**:
- Verify API keys are correct
- Check rate limits
- Ensure fallback LLM is configured

**Voice processing errors**:
- Verify LOCAL_MODELS_DIR exists
- Check model files are downloaded
- Ensure sufficient disk space

## 📞 Support

For issues or questions, refer to:
- API Documentation: http://localhost:8000/docs
- Design Document: `.kiro/specs/medical-ai-platform/design.md`
- Teach-Back Guide: `teach_back/README.md`
