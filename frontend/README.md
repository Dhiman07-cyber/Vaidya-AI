# VaidyaAI Frontend

Next.js frontend for the VaidyaAI Medical AI Platform. Provides comprehensive UI for tutoring, study tools, clinical reasoning, and the Interactive Learning Assistant (Teach-Back Mode).

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend running at http://localhost:8000

### Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment**:
```bash
cp .env.local.example .env.local
# Edit .env.local with:
# - NEXT_PUBLIC_API_URL=http://localhost:8000
# - NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
```

3. **Run development server**:
```bash
npm run dev
```

Frontend available at: http://localhost:3000

## 📁 Project Structure

```
frontend/
├── pages/                       # Next.js pages (file-based routing)
│   ├── _app.tsx                 # App wrapper & providers
│   ├── _document.tsx            # HTML document
│   ├── index.tsx                # Home/landing page
│   ├── login.tsx                # Authentication
│   ├── dashboard.tsx            # User dashboard
│   │
│   ├── chat.tsx                 # Chat/tutoring interface
│   ├── explain.tsx              # Concept explanation
│   │
│   ├── teach-back.tsx           # Interactive Learning Assistant
│   │
│   ├── clinical-reasoning.tsx   # Clinical reasoning simulator
│   ├── clinical-cases.tsx       # Clinical case library
│   ├── clinical.tsx             # Clinical tools
│   │
│   ├── study-tools.tsx          # Study tools hub
│   ├── study-tools/             # Study tool pages
│   │   ├── flashcards.tsx
│   │   ├── mcqs.tsx
│   │   ├── concept-map.tsx
│   │   └── high-yield.tsx
│   ├── flashcards.tsx           # Flashcard viewer
│   ├── mcqs.tsx                 # MCQ practice
│   ├── conceptmap.tsx           # Concept mapping
│   ├── highyield.tsx            # High-yield notes
│   ├── study-planner.tsx        # Study planning
│   │
│   ├── documents.tsx            # Document management
│   │
│   ├── profile.tsx              # User profile
│   ├── upgrade.tsx              # Plan upgrade
│   │
│   ├── admin/                   # Admin panel
│   │   ├── index.tsx            # Admin dashboard
│   │   ├── users.tsx            # User management
│   │   ├── api-keys.tsx         # API key management
│   │   ├── feature-toggles.tsx  # Feature controls
│   │   ├── maintenance.tsx      # Maintenance mode
│   │   └── audit-logs.tsx       # Audit logging
│   │
│   ├── contact.tsx              # Contact page
│   ├── privacy.tsx              # Privacy policy
│   ├── terms.tsx                # Terms of service
│   └── test-components.tsx      # Component testing
│
├── components/                  # React components
│   ├── Layout.tsx               # Main layout wrapper
│   ├── Sidebar.tsx              # Navigation sidebar
│   ├── SessionSidebar.tsx       # Session-specific sidebar
│   │
│   ├── ChatWindow.tsx           # Chat interface
│   ├── ChatInput.tsx            # Chat input component
│   │
│   ├── TeachBack/               # Interactive Learning Assistant
│   │   ├── ModeSelector.tsx     # Input/output mode selection
│   │   ├── LiveTranscript.tsx   # Real-time transcript display
│   │   ├── InterruptionIndicator.tsx  # Error interruption UI
│   │   ├── SessionSummary.tsx   # End-of-session summary
│   │   ├── VoiceControls.tsx    # Voice recording controls
│   │   ├── ExaminationView.tsx  # Q&A examination phase
│   │   └── hooks/
│   │       └── useTeachBackSession.ts  # Session state management
│   │
│   ├── ClinicalMapViewer.tsx    # Clinical concept map
│   ├── FlashcardViewer.tsx      # Flashcard display
│   │
│   ├── StudyToolsLayout.tsx     # Study tools container
│   ├── StudyToolsSidebar.tsx    # Study tools navigation
│   │
│   ├── AdminLayout.tsx          # Admin panel layout
│   ├── AdminSidebar.tsx         # Admin navigation
│   ├── UserList.tsx             # User management
│   ├── ApiKeyList.tsx           # API key management
│   ├── FeatureToggleList.tsx    # Feature toggles
│   ├── MaintenanceControl.tsx   # Maintenance mode control
│   ├── AuditLogTable.tsx        # Audit log display
│   │
│   ├── AuthForm.tsx             # Login/register form
│   ├── UserDetails.tsx          # User profile display
│   ├── DocumentUpload.tsx       # Document upload
│   ├── DocumentList.tsx         # Document listing
│   │
│   ├── DatePicker.tsx           # Date selection
│   ├── TimePicker.tsx           # Time selection
│   │
│   ├── LandingNavbar.tsx        # Landing page navbar
│   ├── LandingFooter.tsx        # Landing page footer
│   │
│   └── ProviderHealthTable.tsx  # Provider status display
│
├── lib/                         # Utility functions
│   ├── supabase.ts              # Supabase client
│   ├── markdown.ts              # Markdown utilities
│   └── [other utilities]
│
├── styles/                      # CSS modules
│   ├── globals.css              # Global styles
│   ├── Layout.module.css
│   ├── Auth.module.css
│   ├── Dashboard.module.css
│   ├── TeachBack.module.css     # Teach-back styles
│   ├── Clinical.module.css
│   ├── StudyTools.module.css
│   ├── Admin.module.css
│   └── [other styles]
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── property/                # Property-based tests
│
├── public/                      # Static assets
│   └── Landing.jpg
│
├── next.config.js              # Next.js configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
├── tsconfig.json               # TypeScript configuration
├── jest.config.js              # Jest configuration
├── jest.setup.js               # Jest setup
└── package.json                # Dependencies
```

## 🎨 Key Features

### 1. **Interactive Learning Assistant (Teach-Back)**
- **Mode Selection**: Choose input (text/voice/mixed) and output (text/voice+text)
- **Live Transcript**: Real-time display of teaching and feedback
- **Error Detection**: Visual indicators when errors are detected
- **Interruption Handling**: Gentle corrections with acknowledgment flow
- **Examination Phase**: OSCE-style Q&A at session end
- **Session Summary**: Comprehensive feedback with recommendations

### 2. **Chat Interface**
- Real-time messaging with AI tutor
- Message history and context
- Markdown support for formatted responses
- Code syntax highlighting

### 3. **Study Tools**
- **Flashcards**: Spaced repetition learning
- **MCQs**: Multiple choice practice with explanations
- **Concept Maps**: Visual knowledge organization
- **High-Yield Notes**: Essential medical concepts
- **Study Planner**: Personalized study scheduling

### 4. **Clinical Reasoning**
- Case-based scenarios
- Differential diagnosis support
- Evidence-based recommendations
- Progress tracking

### 5. **Admin Panel**
- User management
- API key pool management
- Feature toggles
- Maintenance mode control
- Audit logging
- Usage statistics

## 🔧 Configuration

### Environment Variables (`.env.local`)

**Required**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**Optional**:
```bash
NEXT_PUBLIC_APP_NAME=VaidyaAI
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## 🧪 Testing

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run Tests with Coverage
```bash
npm test -- --coverage
```

### Run Specific Test File
```bash
npm test -- ChatWindow.test.tsx
```

### Property-Based Tests
```bash
npm test -- --testPathPattern=property
```

## 🏗️ Building

### Development Build
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Export Static Site
```bash
npm run export
```

## 📚 Component Documentation

### TeachBack Components

**ModeSelector**
- Displays input mode options (Text, Voice, Mixed)
- Displays output mode options (Text, Voice+Text)
- Validates mode compatibility
- Emits selection to parent

**LiveTranscript**
- Real-time transcript display
- Auto-scroll to latest entry
- Speaker identification (user/system)
- Timestamp display
- Syntax highlighting for code

**InterruptionIndicator**
- Visual alert on error detection
- Displays correction text
- Acknowledgment button
- Fade-out animation

**SessionSummary**
- Displays all detected errors
- Lists missed concepts
- Shows strong areas
- Provides recommendations
- Displays examination scores
- Download/save options

**VoiceControls**
- Microphone permission handling
- Record start/stop buttons
- Visual recording indicator
- Audio level display
- Transcription display

**ExaminationView**
- Question display
- Answer input field
- Submit button
- Score display
- Navigation between questions

## 🔐 Security

### Authentication
- JWT tokens via Supabase Auth
- Automatic token refresh
- Secure token storage
- Protected routes

### Authorization
- Role-based access control
- Admin-only pages
- Feature-level permissions
- User data isolation

### Data Protection
- HTTPS only (production)
- Secure API communication
- Input validation
- XSS prevention

## 📊 Performance

### Optimization Techniques
- Code splitting with Next.js
- Image optimization
- CSS-in-JS with modules
- Lazy loading components
- Memoization for expensive computations

### Monitoring
- Error tracking
- Performance metrics
- User analytics
- Feature usage

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Deploy the 'out' directory
```

### Docker
```bash
docker build -t vaidyaai-frontend .
docker run -p 3000:3000 vaidyaai-frontend
```

### Environment Setup
1. Set all required environment variables
2. Build: `npm run build`
3. Start: `npm start`

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for changes
3. Run tests: `npm test`
4. Ensure coverage: `npm test -- --coverage`
5. Commit with clear messages
6. Push and create PR

## 📝 Code Style

- **TypeScript**: Strict mode enabled
- **React**: Functional components with hooks
- **CSS**: CSS Modules for scoping
- **Formatting**: Prettier (configured in package.json)
- **Linting**: ESLint (configured in .eslintrc)

## 🐛 Troubleshooting

### Common Issues

**Port 3000 already in use**:
```bash
# Use different port
npm run dev -- -p 3001
```

**API connection failed**:
- Check NEXT_PUBLIC_API_URL is correct
- Verify backend is running
- Check CORS configuration

**Supabase connection failed**:
- Verify NEXT_PUBLIC_SUPABASE_URL
- Check NEXT_PUBLIC_SUPABASE_ANON_KEY
- Ensure Supabase project is active

**Voice features not working**:
- Check browser supports Web Audio API
- Verify HTTPS in production
- Check microphone permissions
- Ensure backend voice processor is running

## 📖 Additional Documentation

- **Teach-Back Guide**: `components/TeachBack/README.md`
- **Design Document**: `../.kiro/specs/medical-ai-platform/design.md`
- **Backend API**: http://localhost:8000/docs
- **Next.js Docs**: https://nextjs.org/docs

## 📞 Support

For issues or questions, refer to:
- Component documentation in code
- Design Document: `.kiro/specs/medical-ai-platform/design.md`
- Backend API Docs: http://localhost:8000/docs
