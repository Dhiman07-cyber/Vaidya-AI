# Feature-Based Model System ✅

## What Changed

The model system now uses **feature names** instead of generic categories like "chat" and "image". This makes the admin panel API key classification meaningful and allows different models per feature.

## 🎯 How It Works Now

### 1. Each Feature Has Its Own Model

```json
{
  "gemini": {
    "chat": "models/gemini-2.5-flash",
    "flashcard": "models/gemini-2.5-flash",
    "mcq": "models/gemini-2.5-flash",
    "image": "models/gemini-2.5-flash-image"  ← Different!
  }
}
```

### 2. API Keys Are Feature-Specific

When adding API keys in admin panel:

| Feature | Provider | Feature Name | Model Used |
|---------|----------|--------------|------------|
| Chat | `gemini` | `chat` | `gemini-2.5-flash` |
| Flashcards | `gemini` | `flashcard` | `gemini-2.5-flash` |
| MCQ | `gemini` | `mcq` | `gemini-2.5-flash` |
| Image | `gemini` | `image` | `gemini-2.5-flash-image` |

### 3. System Matches Feature → Key → Model

```
User requests flashcard
    ↓
System looks for API key WHERE provider='gemini' AND feature='flashcard'
    ↓
System loads model from models.json: gemini.flashcard
    ↓
Calls API with correct key and model
```

## 💡 Why This Matters

### Before (Generic)
```
Admin adds key:
- Provider: gemini
- Feature: chat  ← Used for everything
- Key: xxx

Problem: Can't separate quotas or use different models
```

### After (Feature-Specific)
```
Admin adds keys:
- Provider: gemini, Feature: chat, Key: xxx
- Provider: gemini, Feature: flashcard, Key: yyy
- Provider: gemini, Feature: mcq, Key: zzz
- Provider: gemini, Feature: image, Key: www

Benefits:
✅ Separate API quotas per feature
✅ Different models per feature
✅ Better cost tracking
✅ Isolate failures
✅ Feature-specific rate limiting
```

## 📝 Example Scenarios

### Scenario 1: Different Models Per Feature

```json
{
  "gemini": {
    "chat": "models/gemini-2.5-flash-lite",      ← Cheap, fast
    "flashcard": "models/gemini-2.5-flash-lite", ← Cheap, fast
    "mcq": "models/gemini-3-pro-preview",        ← Expensive, smart
    "image": "models/gemini-2.5-flash-image"     ← Specialized
  }
}
```

**Result:**
- Chat and flashcards use cheap model (save money)
- MCQ uses expensive model (better quality)
- Image uses specialized model (required)

### Scenario 2: Different Providers Per Feature

Edit `services/model_router.py`:
```python
provider_map = {
    "chat": "gemini",      ← Use Gemini
    "mcq": "openai",       ← Use OpenAI
    "flashcard": "anthropic"  ← Use Claude
}
```

Add API keys:
- Provider: `gemini`, Feature: `chat`
- Provider: `openai`, Feature: `mcq`
- Provider: `anthropic`, Feature: `flashcard`

**Result:** Each feature uses a different AI provider!

### Scenario 3: Quota Management

```
Gemini API Key 1:
- Feature: chat
- Quota: 1M tokens/day
- Usage: High volume

Gemini API Key 2:
- Feature: mcq
- Quota: 100K tokens/day
- Usage: Low volume, high quality

Gemini API Key 3:
- Feature: image
- Quota: 50K tokens/day
- Usage: Specialized
```

**Result:** Each feature has its own quota, no interference!

## 🔧 Configuration Files

### models.json (Feature → Model)
```json
{
  "gemini": {
    "chat": "models/gemini-2.5-flash",
    "flashcard": "models/gemini-2.5-flash",
    "mcq": "models/gemini-2.5-flash",
    "highyield": "models/gemini-2.5-flash",
    "explain": "models/gemini-2.5-flash",
    "map": "models/gemini-2.5-flash",
    "clinical": "models/gemini-2.5-flash",
    "osce": "models/gemini-2.5-flash",
    "image": "models/gemini-2.5-flash-image"
  }
}
```

### model_router.py (Feature → Provider)
```python
provider_map = {
    "chat": "gemini",
    "flashcard": "gemini",
    "mcq": "gemini",
    "highyield": "gemini",
    "explain": "gemini",
    "map": "gemini",
    "image": "gemini",
    "clinical": "gemini",
    "osce": "gemini"
}
```

### Database (API Keys)
```sql
api_keys table:
- provider: 'gemini'
- feature: 'flashcard'  ← Feature-specific!
- key_value: 'encrypted_key'
- status: 'active'
```

## 🚀 Usage in Code

```python
# Old way (deprecated)
from config.model_config import get_gemini_chat_model
model = get_gemini_chat_model()

# New way (feature-specific)
from config.model_config import get_gemini_model
model = get_gemini_model("flashcard")  # Returns model for flashcard feature
```

## 📊 Feature List

All available features:
- `chat` - Chat conversations
- `flashcard` - Flashcard generation
- `mcq` - MCQ generation
- `highyield` - High-yield notes
- `explain` - Concept explanations
- `map` - Concept maps
- `image` - Image analysis
- `clinical` - Clinical cases
- `osce` - OSCE practice

## 🎯 Quick Actions

**Change model for flashcards:**
```json
// Edit backend/models.json
{
  "gemini": {
    "flashcard": "models/gemini-2.5-flash-lite"  ← Change this
  }
}
```

**Add API key for MCQ:**
```
Admin Panel:
- Provider: gemini
- Feature: mcq  ← Use exact feature name
- Key: your-api-key
```

**Use different provider for MCQ:**
```python
// Edit backend/services/model_router.py
provider_map = {
    "mcq": "openai"  ← Change from gemini to openai
}
```

## 🚀 Servers Running

- **Backend**: http://127.0.0.1:8000 ✅
- **Frontend**: http://localhost:3000 ✅
- **Health Checks**: Active ✅
- **Feature-Based Models**: Working ✅

## 📖 Documentation

- **Quick Reference**: `backend/QUICK_FEATURE_REF.md`
- **Detailed Mapping**: `backend/FEATURE_MODEL_MAPPING.md`
- **Flow Diagrams**: `backend/FEATURE_FLOW.md`
- **Model Guide**: `backend/MODELS_README.md`
