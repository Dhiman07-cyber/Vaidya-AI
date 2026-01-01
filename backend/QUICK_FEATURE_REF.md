# Quick Feature Reference

## 🎯 Feature → Model → API Key

| Feature | Provider | Model | API Key Feature |
|---------|----------|-------|-----------------|
| Chat | Gemini | `gemini-2.5-flash` | `chat` |
| Flashcards | Gemini | `gemini-2.5-flash` | `flashcard` |
| MCQ | Gemini | `gemini-2.5-flash` | `mcq` |
| High-Yield | Gemini | `gemini-2.5-flash` | `highyield` |
| Explain | Gemini | `gemini-2.5-flash` | `explain` |
| Concept Map | Gemini | `gemini-2.5-flash` | `map` |
| Image Analysis | Gemini | `gemini-2.5-flash-image` | `image` ⚠️ |
| Clinical Cases | Gemini | `gemini-2.5-flash` | `clinical` |
| OSCE Practice | Gemini | `gemini-2.5-flash` | `osce` |

⚠️ **Image uses a different model!**

## 🔑 Adding API Keys in Admin Panel

Use the **feature name** from the table above:

**Example for Flashcards:**
- Provider: `gemini`
- Feature: `flashcard` ← Use this exact name
- Key: `AIza...`

**Example for Image Analysis:**
- Provider: `gemini`
- Feature: `image` ← Use this exact name
- Key: `AIza...`

## 📝 Changing Models

Edit `backend/models.json`:

```json
{
  "gemini": {
    "flashcard": "models/gemini-2.5-flash-lite",  ← Change this
    "mcq": "models/gemini-3-pro-preview",         ← Or this
    "image": "models/gemini-2.5-flash-image"      ← Keep different
  }
}
```

## 🔄 Why Feature-Specific?

✅ Separate API quotas per feature  
✅ Different models for different needs  
✅ Better cost tracking  
✅ Isolate failures  

## 📚 Full Documentation

- **Detailed Mapping**: `FEATURE_MODEL_MAPPING.md`
- **Flow Diagrams**: `FEATURE_FLOW.md`
- **Model Guide**: `MODELS_README.md`
