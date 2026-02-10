# VaidyaAI - Medical AI Platform

A production-grade AI medical education platform designed for medical students with a scarcity-first engineering approach. Combines AI tutoring, interactive learning, clinical reasoning simulation, and comprehensive study tools.

## 🎯 Core Features

### Learning & Tutoring
- **AI Chat Interface**: Real-time tutoring with multiple LLM providers
- **Interactive Learning Assistant (Teach-Back Mode)**: Practice teaching concepts to an AI tutor with real-time error detection and OSCE-style examination
- **Clinical Reasoning Engine**: Simulate clinical decision-making with case-based learning
- **OSCE Simulator**: Practice objective structured clinical examinations

### Study Tools
- **Flashcards**: Spaced repetition learning with AI-generated cards
- **MCQ Practice**: Multiple choice questions with detailed explanations
- **Concept Maps**: Visual knowledge organization and relationships
- **High-Yield Notes**: Curated essential medical concepts
- **Study Planner**: Personalized study scheduling and progress tracking

### Content Management
- **Document Upload & Processing**: RAG-based document analysis
- **Clinical Case Library**: Real-world clinical scenarios
- **Weak Area Analysis**: Personalized identification of knowledge gaps

### Administration
- **API Key Pool Management**: Manage multiple LLM provider keys
- **Feature Toggles**: Enable/disable features per user
- **Rate Limiting**: Freemium model with plan-based quotas
- **Maintenance Mode**: Automatic failover and graceful degradation
- **Audit Logging**: Complete activity tracking
- **User Management**: Admin controls for users and permissions

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Next.js 14+ (TypeScript, React 18+)
- **Backend**: FastAPI (Python 3.11+, async/await)
- **Database**: Supabase (PostgreSQL + Auth + pgvector)
- **AI Providers**: 
  - Primary: Configurable (OpenRouter, Anthropic, Gemini, etc.)
  - Fallback: m42-health/Llama3-Med42-70B (Hugging Face)
- **Voice Processing**: Whisper-large-v3 (STT), Piper TTS
- **Deployment**: Docker, Hugging Face Spaces ready

### Module Structure

```
VaidyaAI/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── services/                  # Business logic
│   │   ├── auth.py               # Authentication
│   │   ├── chat.py               # Chat service
│   │   ├── clinical.py           # Clinical reasoning
│   │   ├── study_tools.py        # Study tools
│   │   ├── documents.py          # Document processing
│   │   ├── rate_limiter.py       # Rate limiting
│   │   ├── model_router.py       # LLM routing
│   │   ├── admin.py              # Admin operations
│   │   └── providers/            # LLM integrations
│   ├── teach_back/               # Interactive Learning Assistant
│   │   ├── session_manager.py    # Session lifecycle
│   │   ├── state_machine.py      # State management
│   │   ├── llm_orchestrator.py   # Multi-role LLM
│   │   ├── voice_processor.py    # STT/TTS
│   │   ├── rate_limiter.py       # Independent quotas
│   │   ├── roles/                # AI roles
│   │   ├── routes.py             # API endpoints
│   │   └── admin_routes.py       # Admin controls
│   ├── middleware/               # Custom middleware
│   ├── config/                   # Configuration
│   ├── database/                 # DB utilities
│   └── tests/                    # Test suite
├── frontend/
│   ├── pages/                    # Next.js pages
│   │   ├── teach-back.tsx        # Interactive learning
│   │   ├── chat.tsx              # Chat interface
│   │   ├── clinical-reasoning.tsx
│   │   ├── study-tools.tsx
│   │   └── admin/                # Admin panel
│   ├── components/
│   │   ├── TeachBack/            # Teach-back UI
│   │   ├── ChatWindow.tsx
│   │   ├── StudyToolsLayout.tsx
│   │   └── AdminLayout.tsx
│   ├── lib/                      # Utilities
│   └── tests/                    # Test suite
└── docs/                         # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account
- Git

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials and LLM API keys
uvicorn main:app --reload
```

Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with backend URL and Supabase credentials
npm run dev
```

Frontend: http://localhost:3000

### Database Setup

```bash
# Run migrations (handled automatically on startup)
# Or manually:
cd backend
python run_migration.py
```

## 📚 Documentation

### Core Documentation
- **Design Document**: `.kiro/specs/medical-ai-platform/design.md`
- **Requirements**: `.kiro/specs/medical-ai-platform/requirements.md`
- **Implementation Tasks**: `.kiro/specs/medical-ai-platform/tasks.md`

### Feature Documentation
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`
- **Teach-Back Module**: `backend/teach_back/README.md`
- **Deployment Guide**: `docs/teach_back_deployment.md`

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## 🧪 Testing

### Backend Tests
```bash
cd backend

# All tests
pytest

# Property-based tests (29 properties, 100 iterations each)
pytest tests/property/ -v

# With coverage report
pytest --cov=backend --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py -v
```

### Frontend Tests
```bash
cd frontend

# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm test -- --coverage
```

### Integration Tests
```bash
cd backend

# End-to-end session flow
pytest tests/integration/test_teach_back_e2e.py -v

# All integration tests
pytest tests/integration/ -v
```

## 🔧 Development Workflow

### 1. Local Development
- Start backend: `cd backend && uvicorn main:app --reload`
- Start frontend: `cd frontend && npm run dev`
- Access at http://localhost:3000

### 2. Feature Development
- Follow task phases in implementation plan
- Write tests alongside code
- Use property-based tests for correctness
- Commit frequently with clear messages

### 3. Testing Strategy
- **Unit Tests**: Specific examples and edge cases
- **Property Tests**: Universal correctness properties (100 iterations)
- **Integration Tests**: Complete feature workflows
- **Manual Testing**: UI/UX validation

### 4. Code Quality
- Type checking: `mypy backend/` (Python)
- Linting: `pylint backend/` (Python)
- Format: `black backend/` (Python)
- TypeScript: `tsc --noEmit` (Frontend)

## 📊 Key Features Explained

### Interactive Learning Assistant (Teach-Back Mode)
Students teach concepts to an AI tutor that:
- Acts as a curious junior medical student
- Detects conceptual errors in real-time
- Provides gentle, constructive corrections
- Conducts OSCE-style examination at session end
- Generates personalized study recommendations

**Modes**:
- Input: Text Only, Voice Only, Text+Voice Mixed
- Output: Text Only, Voice+Text
- Automatic transcription and synthesis

**Rate Limits** (per plan):
- Free: Disabled
- Student: 5 text/day, 2 voice/day
- Pro: 20 text/day, 10 voice/day
- Admin: Unlimited

### Clinical Reasoning Engine
Simulates clinical decision-making with:
- Case-based scenarios
- Differential diagnosis support
- Evidence-based recommendations
- Performance tracking

### Study Tools
- **Flashcards**: AI-generated from weak areas
- **MCQs**: Targeted practice on knowledge gaps
- **Concept Maps**: Visual knowledge organization
- **High-Yield Notes**: Essential medical concepts

## 🔐 Security & Privacy

- **Authentication**: Supabase Auth (JWT tokens)
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: End-to-end encryption for sensitive data
- **Rate Limiting**: Per-user and per-feature quotas
- **Audit Logging**: Complete activity tracking
- **HIPAA Compliance**: Ready for healthcare deployment

## 📈 Monitoring & Analytics

### Key Metrics
- Session creation and completion rates
- Feature usage by plan
- LLM provider performance
- Error rates and types
- User engagement metrics
- Study progress tracking

### Admin Dashboard
- Real-time usage statistics
- Error monitoring and alerts
- LLM failover tracking
- Maintenance mode status
- User management
- Feature toggle controls

## 🚢 Deployment

### Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Production
See `docs/teach_back_deployment.md` for complete deployment guide:
- Docker containerization
- Environment configuration
- Database migrations
- Model downloads (Whisper, Piper)
- Monitoring setup
- Troubleshooting

### Hugging Face Spaces
- Ready for deployment
- Automatic model downloads
- Resource-aware configuration
- Secrets management

## 📝 Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# Supabase
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...

# LLM Configuration
TEACH_BACK_PRIMARY_LLM_PROVIDER=openrouter
TEACH_BACK_PRIMARY_LLM_MODEL=anthropic/claude-3.5-sonnet
TEACH_BACK_PRIMARY_LLM_KEY=sk-...
TEACH_BACK_FALLBACK_LLM_KEY=hf_...

# Local Models
LOCAL_MODELS_DIR=/local_models

# Feature Flags
TEACH_BACK_ENABLED=true
TEACH_BACK_VOICE_ENABLED=true
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Write tests for your changes
3. Ensure all tests pass: `pytest` (backend), `npm test` (frontend)
4. Commit with clear messages
5. Push and create a pull request

## 📄 License

Proprietary - All rights reserved. VaidyaAI Medical Platform.

## 📞 Support

For issues, questions, or feature requests, please refer to the documentation or contact the development team.
